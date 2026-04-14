"""
Context Compactor Service

Handles rolling compression of chat context using chain-based summaries.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from open_webui.models.chat_context_segments import (
    ChatContextSegments,
    ChatContextSegmentModel,
)
from open_webui.models.chat_context_state import (
    ChatContextStates,
    ChatContextStateModel,
)
from open_webui.models.chats import Chats
from open_webui.utils.tool_digest_builder import (
    ToolDigestBuilder,
    extract_tool_digest_from_messages,
)
from open_webui.utils.chat_summarizer import extract_messages_from_chat

log = logging.getLogger(__name__)

# Prompt for context summarization - simplified for better compatibility
CONTEXT_SUMMARIZATION_PROMPT = """Создай краткое резюме диалога.

{previous_summary_section}

НОВЫЕ СООБЩЕНИЯ:
{new_messages}

{tool_digest_section}

Ответь в формате JSON:
{{
  "short_summary": "краткое описание диалога",
  "facts": ["факт 1", "факт 2"],
  "decisions": ["решение 1"],
  "open_questions": ["вопрос 1"],
  "tool_digest": []
}}

Важно: только JSON, без markdown, без текста до или после.
"""

PREVIOUS_SUMMARY_SECTION = """ПРЕДЫДУЩИЙ SUMMARY (уже сжатая часть разговора):
{previous_summary}

Этот summary содержит сжатую информацию о предыдущей части диалога. Объедини её с новыми сообщениями."""

TOOL_DIGEST_SECTION = """TOOL ВЫЗОВЫ:
{tool_digest}

Эти tool вызовы были сделаны в новых сообщениях. Включи их результаты в summary."""


class ContextCompactor:
    """Handles compaction of chat context into chain-based summaries."""

    def __init__(self):
        self.tool_builder = ToolDigestBuilder()

    async def compact_chat_context(
        self,
        request,
        chat_id: str,
        user_id: str,
        force: bool = False,
        user: Optional[Any] = None,
    ) -> Optional[ChatContextSegmentModel]:
        """
        Main entry point for context compaction.

        Args:
            request: FastAPI request object (for LLM calls)
            chat_id: Chat ID to compact
            user_id: User ID
            force: Force compaction even if thresholds not met
            user: User object (optional, for background tasks)

        Returns:
            New segment if compaction was performed, None otherwise
        """
        try:
            # Get or create state
            state = ChatContextStates.get_or_create_state(chat_id, user_id)

            # Check if compaction is enabled
            if not state.enabled and not force:
                log.debug(f"Compaction disabled for chat {chat_id}")
                return None

            # Get chat data
            chat = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
            if not chat:
                log.warning(f"Chat {chat_id} not found for user {user_id}")
                return None

            # Extract all messages
            messages = self._extract_messages(chat.chat)
            if not messages:
                log.debug(f"No messages to compact in chat {chat_id}")
                return None

            # Determine which messages need compaction
            messages_to_compact, raw_messages = self._split_messages(
                messages, state.last_compacted_message_id, state.keep_last_messages
            )

            if not messages_to_compact:
                log.debug(f"No messages to compact in chat {chat_id}")
                return None

            # Check thresholds
            if not force:
                token_count = self._estimate_tokens(messages_to_compact)
                if not ChatContextStates.should_compact(
                    chat_id, len(messages_to_compact), token_count
                ):
                    log.debug(
                        f"Thresholds not met for chat {chat_id}: "
                        f"{len(messages_to_compact)} messages, {token_count} tokens"
                    )
                    return None

            # Get previous segment for chaining
            previous_segment = None
            if state.active_segment_id:
                previous_segment = ChatContextSegments.get_segment_by_id(
                    state.active_segment_id
                )

            # Extract tool digest
            tool_digest = []
            if state.include_tool_data:
                tool_digest = extract_tool_digest_from_messages(messages_to_compact)

            # Build compaction input
            compaction_input = self._build_compaction_input(
                previous_segment, messages_to_compact, tool_digest
            )

            # Call LLM to generate summary
            summary_data = await self._call_summarizer(request, compaction_input, user=user, user_id=user_id)
            if not summary_data:
                log.error(f"Failed to generate summary for chat {chat_id}")
                # Create fallback summary from messages
                summary_text = self._create_fallback_summary(messages_to_compact)
                summary_data = {
                    'short_summary': summary_text,
                    'facts': [],
                    'decisions': [],
                    'open_questions': [],
                    'tool_digest': tool_digest if state.include_tool_data else [],
                }
                log.info(f"Using fallback summary for chat {chat_id}")

            # Calculate token counts
            token_count_before = self._estimate_tokens(messages_to_compact)
            token_count_after = self._estimate_summary_tokens(summary_data)

            # Get message IDs for range
            from_message_id = messages_to_compact[0].get('id', '')
            to_message_id = messages_to_compact[-1].get('id', '')

            # Prepare tool_digest - ensure it's a list of dicts
            final_tool_digest = summary_data.get('tool_digest', tool_digest)
            if final_tool_digest and isinstance(final_tool_digest, list):
                # Filter out any non-dict items (strings, etc.)
                final_tool_digest = [item for item in final_tool_digest if isinstance(item, dict)]
            else:
                final_tool_digest = []

            # Create new segment
            new_segment = ChatContextSegments.insert_new_segment(
                chat_id=chat_id,
                user_id=user_id,
                from_message_id=from_message_id,
                to_message_id=to_message_id,
                summary_text=summary_data.get('short_summary', ''),
                summary_json={
                    'short_summary': summary_data.get('short_summary', ''),
                    'facts': summary_data.get('facts', []),
                    'decisions': summary_data.get('decisions', []),
                    'open_questions': summary_data.get('open_questions', []),
                },
                tool_digest_json=final_tool_digest,
                token_count_before=token_count_before,
                token_count_after=token_count_after,
                parent_segment_id=previous_segment.id if previous_segment else None,
                ttl_days=state.max_segment_age_days,
            )

            if not new_segment:
                log.error(f"Failed to create segment for chat {chat_id}")
                return None

            # Mark previous segment as superseded
            if previous_segment:
                ChatContextSegments.supersede_segment(previous_segment.id)

            # Update state
            ChatContextStates.update_state(
                chat_id=chat_id,
                last_compacted_message_id=to_message_id,
                active_segment_id=new_segment.id,
            )

            # Cleanup old segments
            self._cleanup_old_segments(chat_id, state.max_segments_per_chat)

            log.info(
                f"Created segment {new_segment.id} for chat {chat_id}: "
                f"{token_count_before} -> {token_count_after} tokens "
                f"({len(messages_to_compact)} messages)"
            )

            return new_segment

        except Exception as e:
            log.exception(f"Error compacting chat {chat_id}: {e}")
            return None

    def _extract_messages(self, chat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract messages from chat data with IDs."""
        messages = []

        history = chat_data.get('history', {})
        msg_dict = history.get('messages', {})
        current_id = history.get('currentId')

        if not msg_dict or not current_id:
            return []

        # Build message chain backwards from currentId
        visited = set()
        msg_chain = []

        while current_id and current_id not in visited:
            visited.add(current_id)
            msg = msg_dict.get(current_id)

            if not msg:
                break

            # Add ID to message for tracking
            msg_with_id = dict(msg)
            msg_with_id['id'] = current_id
            msg_chain.append(msg_with_id)

            current_id = msg.get('parentId')

        # Reverse to get chronological order
        msg_chain.reverse()

        # Filter to user/assistant messages only
        for msg in msg_chain:
            role = msg.get('role', '')
            if role in ('user', 'assistant', 'tool'):
                messages.append(msg)

        return messages

    def _split_messages(
        self,
        messages: List[Dict[str, Any]],
        last_compacted_id: Optional[str],
        keep_last: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split messages into those to compact and those to keep raw.

        Returns:
            Tuple of (messages_to_compact, raw_messages_to_keep)
        """
        if not messages:
            return [], []

        # Find index of last compacted message
        compacted_idx = -1
        if last_compacted_id:
            for i, msg in enumerate(messages):
                if msg.get('id') == last_compacted_id:
                    compacted_idx = i
                    break

        # Messages after last_compacted_id need to be considered
        if compacted_idx >= 0:
            candidate_messages = messages[compacted_idx + 1:]
        else:
            candidate_messages = messages

        # Keep last N messages raw, compact the rest
        if len(candidate_messages) <= keep_last:
            return [], candidate_messages

        messages_to_compact = candidate_messages[:-keep_last]
        raw_messages = candidate_messages[-keep_last:]

        return messages_to_compact, raw_messages

    def _build_compaction_input(
        self,
        previous_segment: Optional[ChatContextSegmentModel],
        new_messages: List[Dict[str, Any]],
        tool_digest: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build input for the summarizer LLM."""
        # Format previous summary section
        previous_summary_section = ""
        if previous_segment:
            prev_summary = previous_segment.summary_json
            prev_text = prev_summary.get('short_summary', '')
            prev_facts = '\n'.join(f'- {f}' for f in prev_summary.get('facts', []))
            prev_decisions = '\n'.join(f'- {d}' for d in prev_summary.get('decisions', []))

            previous_summary_text = f"""Summary: {prev_text}

Key Facts:
{prev_facts}

Decisions:
{prev_decisions}"""

            previous_summary_section = PREVIOUS_SUMMARY_SECTION.format(
                previous_summary=previous_summary_text
            )

        # Format new messages
        formatted_messages = []
        for msg in new_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            # Handle different content formats
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                content = ' '.join(text_parts)
            elif isinstance(content, dict):
                content = content.get('text', str(content))

            formatted_messages.append(f"{role.upper()}: {content}")

        new_messages_text = '\n\n'.join(formatted_messages)

        # Format tool digest section
        tool_digest_section = ""
        if tool_digest:
            tool_lines = []
            for tool in tool_digest:
                tool_lines.append(
                    f"- {tool['tool_name']}: {tool['arguments_summary']} -> "
                    f"{tool['result_summary']} ({tool['status']})"
                )
            tool_digest_section = TOOL_DIGEST_SECTION.format(
                tool_digest='\n'.join(tool_lines)
            )

        return {
            'previous_summary_section': previous_summary_section,
            'new_messages': new_messages_text,
            'tool_digest_section': tool_digest_section,
        }

    async def _call_summarizer(
        self,
        request,
        input_data: Dict[str, str],
        user: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Call LLM to generate summary."""
        try:
            # Build prompt
            prompt = CONTEXT_SUMMARIZATION_PROMPT.format(
                previous_summary_section=input_data['previous_summary_section'],
                new_messages=input_data['new_messages'],
                tool_digest_section=input_data['tool_digest_section'],
            )

            # Get task model
            from open_webui.config import TASK_MODEL, TASK_MODEL_EXTERNAL
            from open_webui.utils.models import get_all_base_models
            from open_webui.utils.task import get_task_model_id

            # Load models
            try:
                base_models = await get_all_base_models(request, user=user)
                models = {model['id']: model for model in base_models}
                request.app.state.MODELS = models
                request.app.state.BASE_MODELS = base_models
            except Exception as e:
                log.error(f"Failed to load models: {e}")
                models = {}

            if not models:
                log.error("No models available for summarization")
                return None

            default_model_id = list(models.keys())[0]
            task_model_id = get_task_model_id(
                default_model_id,
                TASK_MODEL,
                TASK_MODEL_EXTERNAL,
                models,
            )

            # Call LLM
            from open_webui.utils.chat import generate_chat_completion
            from open_webui.models.users import Users

            # Get user from request if not provided
            if not user:
                if hasattr(request, 'state') and hasattr(request.state, 'user'):
                    user = request.state.user
                elif hasattr(request.app.state, 'user'):
                    user = request.app.state.user

            if not user and user_id:
                # Try to get from user_id parameter
                user = Users.get_user_by_id(user_id)

            if not user:
                # Try to get from request.user_id attribute
                req_user_id = getattr(request, 'user_id', None)
                if req_user_id:
                    user = Users.get_user_by_id(req_user_id)

            if not user:
                log.error("No user found for summarization")
                return None

            payload = {
                'model': task_model_id,
                'messages': [{'role': 'user', 'content': prompt}],
                'stream': False,
                'max_completion_tokens': 3000,
            }

            response = await generate_chat_completion(
                request, form_data=payload, user=user
            )

            # Parse response
            if hasattr(response, 'body'):
                body = await response.body.read()
                content = json.loads(body.decode())
            else:
                content = response

            # Extract generated text
            if isinstance(content, dict):
                if 'choices' in content and len(content['choices']) > 0:
                    generated_text = content['choices'][0].get('message', {}).get('content', '')
                elif 'content' in content:
                    generated_text = content['content']
                else:
                    generated_text = str(content)
            else:
                generated_text = str(content)

            # Parse JSON from response
            log.debug(f"Generated summary text: {generated_text[:500]}...")
            result = self._parse_summary_response(generated_text)
            if result:
                log.info(f"Successfully parsed summary with keys: {list(result.keys())}")
            else:
                log.warning(f"Failed to parse summary from text: {generated_text[:1000]}")
            return result

        except Exception as e:
            log.exception(f"Error calling summarizer: {e}")
            return None

    def _parse_summary_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        try:
            text = text.strip()

            # Remove markdown code blocks
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]

            if text.endswith('```'):
                text = text[:-3]

            text = text.strip()

            # Fix common JSON issues from LLM responses
            # Replace single quotes with double quotes (but not within strings)
            # This is a simple fix - more robust parsing would require a proper JSON5 parser
            import re

            # First, try to parse as-is
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Try to fix common issues
                # Replace single quotes that are used as JSON delimiters
                # Pattern: match single quotes that are at start of value or after punctuation
                fixed_text = text.replace("'", '"')
                try:
                    data = json.loads(fixed_text)
                    log.debug("Fixed JSON by replacing single quotes with double quotes")
                except json.JSONDecodeError:
                    # Try to extract JSON object using regex
                    json_match = re.search(r'\{[\s\S]*\}', text)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            log.debug("Extracted JSON object using regex")
                        except json.JSONDecodeError:
                            # Last resort: try with fixed quotes
                            fixed_json = json_match.group().replace("'", '"')
                            data = json.loads(fixed_json)
                            log.debug("Extracted and fixed JSON object")
                    else:
                        raise

            # Validate and set defaults
            if 'short_summary' not in data or not data['short_summary'] or data.get('error'):
                # LLM returned error or empty summary
                log.warning(f"LLM returned error or empty summary: {data.get('error', 'empty short_summary')}")
                return None

            if 'facts' not in data:
                data['facts'] = []

            if 'decisions' not in data:
                data['decisions'] = []

            if 'open_questions' not in data:
                data['open_questions'] = []

            if 'tool_digest' not in data:
                data['tool_digest'] = []

            return data

        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON from response: {e}")
            log.warning(f"Raw response text: {text[:1000]}...")
            return None
        except Exception as e:
            log.exception(f"Error parsing summary response: {e}")
            log.warning(f"Raw response text: {text[:1000]}...")
            return None

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Rough estimate of token count for messages."""
        total_chars = 0
        for msg in messages:
            content = msg.get('content', '')
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        total_chars += len(item['text'])
            elif isinstance(content, dict):
                total_chars += len(str(content))

        # Rough estimate: 1 token ≈ 4 characters
        return total_chars // 4

    def _estimate_summary_tokens(self, summary_data: Dict[str, Any]) -> int:
        """Rough estimate of token count for summary."""
        text = json.dumps(summary_data, ensure_ascii=False)
        return len(text) // 4

    def _cleanup_old_segments(self, chat_id: str, max_segments: int):
        """Cleanup old segments for a chat."""
        try:
            deleted = ChatContextSegments.cleanup_old_segments_by_chat(
                chat_id, keep_count=max_segments
            )
            if deleted > 0:
                log.debug(f"Cleaned up {deleted} old segments for chat {chat_id}")
        except Exception as e:
            log.warning(f"Error cleaning up old segments: {e}")

    def _create_fallback_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create a fallback summary from messages when LLM fails."""
        # Extract first user message as topic
        topic = "Чат"
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, str):
                    topic = content[:100] + "..." if len(content) > 100 else content
                break

        # Count messages by role
        user_count = sum(1 for m in messages if m.get('role') == 'user')
        assistant_count = sum(1 for m in messages if m.get('role') == 'assistant')

        return f"Диалог на тему: {topic}. Содержит {user_count} сообщений пользователя и {assistant_count} ответов ассистента."


# Global instance
_context_compactor: Optional[ContextCompactor] = None


def get_context_compactor() -> ContextCompactor:
    """Get or create global context compactor instance."""
    global _context_compactor
    if _context_compactor is None:
        _context_compactor = ContextCompactor()
    return _context_compactor


async def compact_chat_context(
    request,
    chat_id: str,
    user_id: str,
    force: bool = False,
) -> Optional[ChatContextSegmentModel]:
    """Convenience function to compact chat context."""
    compactor = get_context_compactor()
    return await compactor.compact_chat_context(request, chat_id, user_id, force)
