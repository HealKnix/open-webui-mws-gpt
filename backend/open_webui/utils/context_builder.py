"""
Context Builder Module

Builds the final context for LLM by combining:
- System prompt
- Compressed summary (active segment)
- Tool digest
- Recent raw messages
"""

import json
import logging
from typing import Dict, List, Any, Optional

from open_webui.models.chat_context_segments import ChatContextSegments
from open_webui.models.chat_context_state import ChatContextStates
from open_webui.models.chats import Chats

log = logging.getLogger(__name__)


class ContextBuilder:
    """Builds chat context for LLM with compression support."""

    def __init__(self):
        pass

    def build_chat_context(
        self,
        chat_id: str,
        user_id: str,
        system_prompt: Optional[str] = None,
        include_summary: bool = True,
        include_tool_digest: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Build the complete context for LLM.

        Args:
            chat_id: Chat ID
            user_id: User ID
            system_prompt: Original system prompt (if any)
            include_summary: Whether to include compressed summary
            include_tool_digest: Whether to include tool digest

        Returns:
            List of messages ready for LLM
        """
        result = []

        # 1. Add system prompt if provided
        if system_prompt:
            result.append({
                'role': 'system',
                'content': system_prompt,
            })

        # Get state to check if compression is enabled
        state = ChatContextStates.get_state_by_chat_id(chat_id)

        if not state or not state.enabled:
            # Compression disabled or not configured, return empty context
            # (caller should use full message history)
            return result

        # 2. Add compressed summary if available
        if include_summary and state.active_segment_id:
            summary_message = self._build_summary_message(
                state.active_segment_id,
                include_tool_digest and state.include_tool_data,
            )
            if summary_message:
                result.append(summary_message)

        return result

    def _build_summary_message(
        self,
        segment_id: str,
        include_tool_digest: bool,
    ) -> Optional[Dict[str, Any]]:
        """Build a system message with compressed summary."""
        segment = ChatContextSegments.get_segment_by_id(segment_id)
        if not segment:
            return None

        # Build XML-formatted summary
        summary_xml = self._format_summary_as_xml(segment, include_tool_digest)

        return {
            'role': 'system',
            'content': summary_xml,
        }

    def _format_summary_as_xml(
        self,
        segment: Any,  # ChatContextSegmentModel
        include_tool_digest: bool,
    ) -> str:
        """
        Format segment summary as plain text for LLM understanding.
        """
        summary_json = segment.summary_json

        lines = ['=== ПРЕДЫДУЩИЙ КОНТЕКСТ (сжатый) ===', '']

        # Short summary
        short_summary = summary_json.get('short_summary', '')
        if short_summary:
            lines.append(f'Краткое содержание: {short_summary}')
            lines.append('')

        # Facts
        facts = summary_json.get('facts', [])
        if facts:
            lines.append('Важные факты:')
            for i, fact in enumerate(facts, 1):
                lines.append(f'  {i}. {fact}')
            lines.append('')

        # Decisions
        decisions = summary_json.get('decisions', [])
        if decisions:
            lines.append('Принятые решения:')
            for i, decision in enumerate(decisions, 1):
                lines.append(f'  {i}. {decision}')
            lines.append('')

        # Open questions
        open_questions = summary_json.get('open_questions', [])
        if open_questions:
            lines.append('Открытые вопросы:')
            for i, question in enumerate(open_questions, 1):
                lines.append(f'  {i}. {question}')
            lines.append('')

        # Tool digest
        if include_tool_digest and segment.tool_digest_json:
            tool_text = self._format_tool_digest_as_text(segment.tool_digest_json)
            if tool_text:
                lines.append(tool_text)

        lines.append('=== КОНЕЦ ПРЕДЫДУЩЕГО КОНТЕКСТА ===')

        return '\n'.join(lines)

    def _format_tool_digest_as_text(self, tool_digest: List[Dict[str, Any]]) -> str:
        """Format tool digest as plain text."""
        if not tool_digest:
            return ''

        lines = ['Выполненные действия:']

        for i, tool in enumerate(tool_digest, 1):
            tool_name = tool.get('tool_name', 'unknown')
            status = tool.get('status', 'unknown')
            args = tool.get('arguments_summary', '')
            result = tool.get('result_summary', '')

            lines.append(f'  {i}. {tool_name} ({status})')
            if args:
                lines.append(f'     Аргументы: {args}')
            if result:
                lines.append(f'     Результат: {result}')

        return '\n'.join(lines)

    def _format_tool_digest_as_xml(self, tool_digest: List[Dict[str, Any]]) -> str:
        """
        Format tool digest as XML.

        Format:
        <tool_context>
          <tool name="..." status="...">
            <arguments>...</arguments>
            <result>...</result>
          </tool>
        </tool_context>
        """
        if not tool_digest:
            return ''

        lines = ['<tool_context>']

        for tool in tool_digest:
            tool_name = tool.get('tool_name', 'unknown')
            status = tool.get('status', 'unknown')

            lines.append(f'  <tool name="{self._escape_xml_attr(tool_name)}" status="{self._escape_xml_attr(status)}">')

            # Arguments
            args = tool.get('arguments_summary', '')
            if args:
                lines.append(f'    <arguments>{self._escape_xml(args)}</arguments>')

            # Result
            result = tool.get('result_summary', '')
            if result:
                lines.append(f'    <result>{self._escape_xml(result)}</result>')

            # Key results from structured data
            key_results = tool.get('key_results', [])
            if key_results:
                lines.append('    <key_results>')
                for kr in key_results:
                    lines.append(f'      <item>{self._escape_xml(kr)}</item>')
                lines.append('    </key_results>')

            # Artifacts
            artifacts = tool.get('artifacts', [])
            if artifacts:
                lines.append('    <artifacts>')
                for artifact in artifacts[:5]:  # Limit to 5
                    lines.append(f'      <artifact>{self._escape_xml(str(artifact))}</artifact>')
                lines.append('    </artifacts>')

            lines.append('  </tool>')

        lines.append('</tool_context>')

        return '\n'.join(lines)

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters in text content."""
        if not text:
            return ''

        # Replace special characters
        text = text.replace('&', '&')
        text = text.replace('<', '<')
        text = text.replace('>', '>')

        return text

    def _escape_xml_attr(self, text: str) -> str:
        """Escape special XML characters in attribute values."""
        if not text:
            return ''

        text = self._escape_xml(text)
        text = text.replace('"', '"')

        return text

    def get_raw_messages_after_compaction(
        self,
        chat_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get raw messages that should be sent after the compressed summary.

        Returns:
            List of recent messages that haven't been compacted yet
        """
        # Get chat data
        chat = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
        if not chat:
            return []

        # Get state
        state = ChatContextStates.get_state_by_chat_id(chat_id)
        if not state:
            # No compaction state, return all messages
            return self._extract_all_messages(chat.chat)

        # Extract messages after last_compacted_message_id
        return self._extract_messages_after(
            chat.chat,
            state.last_compacted_message_id,
            state.keep_last_messages,
        )

    def _extract_all_messages(self, chat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all messages from chat data."""
        messages = []

        history = chat_data.get('history', {})
        msg_dict = history.get('messages', {})
        current_id = history.get('currentId')

        if not msg_dict or not current_id:
            return []

        # Build message chain
        visited = set()
        msg_chain = []

        while current_id and current_id not in visited:
            visited.add(current_id)
            msg = msg_dict.get(current_id)

            if not msg:
                break

            msg_chain.append(msg)
            current_id = msg.get('parentId')

        # Reverse to get chronological order
        msg_chain.reverse()

        # Filter to user/assistant messages
        for msg in msg_chain:
            role = msg.get('role', '')
            if role in ('user', 'assistant'):
                messages.append({
                    'role': role,
                    'content': msg.get('content', ''),
                })

        return messages

    def _extract_messages_after(
        self,
        chat_data: Dict[str, Any],
        last_compacted_id: Optional[str],
        keep_last: int,
    ) -> List[Dict[str, Any]]:
        """Extract messages after the last compacted message."""
        messages = []

        history = chat_data.get('history', {})
        msg_dict = history.get('messages', {})
        current_id = history.get('currentId')

        if not msg_dict or not current_id:
            return []

        # Build message chain
        visited = set()
        msg_chain = []

        while current_id and current_id not in visited:
            visited.add(current_id)
            msg = msg_dict.get(current_id)

            if not msg:
                break

            msg_chain.append(msg)
            current_id = msg.get('parentId')

        # Reverse to get chronological order
        msg_chain.reverse()

        # Find index of last compacted message
        compacted_idx = -1
        if last_compacted_id:
            for i, msg in enumerate(msg_chain):
                if msg.get('id') == last_compacted_id:
                    compacted_idx = i
                    break

        # Get messages after last_compacted_id
        if compacted_idx >= 0:
            recent_messages = msg_chain[compacted_idx + 1:]
        else:
            recent_messages = msg_chain

        # Keep only last N messages
        recent_messages = recent_messages[-keep_last:] if keep_last > 0 else recent_messages

        # Format messages
        for msg in recent_messages:
            role = msg.get('role', '')
            if role not in ('user', 'assistant'):
                continue

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

            messages.append({
                'role': role,
                'content': content,
            })

        return messages

    def build_full_context(
        self,
        chat_id: str,
        user_id: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build the full context including compressed summary and recent messages.

        This is the main method to use when preparing context for LLM.

        Args:
            chat_id: Chat ID
            user_id: User ID
            system_prompt: Original system prompt

        Returns:
            Complete list of messages for LLM
        """
        # Build compressed context
        context = self.build_chat_context(
            chat_id=chat_id,
            user_id=user_id,
            system_prompt=system_prompt,
            include_summary=True,
            include_tool_digest=True,
        )

        # Add recent raw messages
        raw_messages = self.get_raw_messages_after_compaction(chat_id, user_id)
        context.extend(raw_messages)

        return context


# Global instance
_context_builder: Optional[ContextBuilder] = None


def get_context_builder() -> ContextBuilder:
    """Get or create global context builder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder


def build_chat_context(
    chat_id: str,
    user_id: str,
    system_prompt: Optional[str] = None,
    include_summary: bool = True,
    include_tool_digest: bool = True,
) -> List[Dict[str, Any]]:
    """Convenience function to build chat context."""
    builder = get_context_builder()
    return builder.build_chat_context(
        chat_id=chat_id,
        user_id=user_id,
        system_prompt=system_prompt,
        include_summary=include_summary,
        include_tool_digest=include_tool_digest,
    )
