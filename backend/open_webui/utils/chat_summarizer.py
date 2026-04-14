"""
Chat Summarizer Module

Automatically generates summaries from chat conversations and extracts insights.
Uses the same LLM as title generation for consistency.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from open_webui.models.chats import Chats
from open_webui.models.chat_summaries import ChatSummaries
from open_webui.models.memories import Memories
from open_webui.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_webui.utils.task import get_task_model_id

log = logging.getLogger(__name__)

# Prompt for extracting insights and generating summaries
CHAT_SUMMARIZATION_PROMPT = """Проанализируй этот чат и извлеки важную информацию для долгосрочной памяти.

ИСТОРИЯ ЧАТА:
{chat_history}

ЗАДАЧА:
1. Создай КРАТКОЕ саммари чата (2-3 предложения) - о чём был разговор
2. Извлеки ключевые инсайты в одной из категорий:

КАТЕГОРИИ ИНСАЙТОВ:

A. USER_PREFERENCE (предпочтения пользователя):
   - Стиль общения, обращение
   - Жёсткие правила ("никогда не...", "всегда...")
   - Профессиональные предпочтения
   - Примеры: "предпочитает краткие ответы", "работает только с 1С"

B. PROBLEM_SOLUTION (проблема и решение):
   - Технические проблемы + их решения
   - Ошибки и фиксы
   - Best practices
   - Примеры: "ошибка с СКД → использовать ПолучитьМакет()"

C. PROJECT_CONTEXT (контекст проекта):
   - Детали текущих проектов
   - Архитектурные решения
   - Специфика окружения
   - Примеры: "настраивает Docker для Open WebUI"

D. SKIP (не сохранять):
   - Разовые вопросы без долгосрочной ценности
   - Общая информация

ВЕРНИ JSON:
{{
  "summary": "краткое описание чата",
  "category": "coding_1c|docker|general|...",
  "tags": ["тег1", "тег2"],
  "insights": [
    {{
      "type": "USER_PREFERENCE|PROBLEM_SOLUTION|PROJECT_CONTEXT|SKIP",
      "content": "описание инсайта",
      "importance": 0.0-1.0
    }}
  ]
}}

Правила:
- Всегда отвечай на русском языке
- Будь конкретным, избегай общих фраз
- Importance: 0.9+ для критичных правил, 0.5-0.7 для обычных инсайтов
"""


async def generate_chat_summary(
    request,
    chat_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Generate a summary and extract insights from a chat.

    Uses the title generation model for consistency.
    """
    try:
        # Get chat data
        chat = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
        if not chat:
            log.warning(f"Chat {chat_id} not found for user {user_id}")
            return None

        # Extract messages from chat history
        messages = extract_messages_from_chat(chat.chat)
        if len(messages) < 3:
            log.info(f"Chat {chat_id} has too few messages ({len(messages)}), skipping")
            return None

        # Format chat history for the prompt
        chat_history = format_chat_history(messages)

        # Get the task model (same as title generation)
        from open_webui.config import (
            TASK_MODEL,
            TASK_MODEL_EXTERNAL,
        )
        from open_webui.utils.models import get_all_base_models

        # Load models directly (for background task context)
        try:
            base_models = await get_all_base_models(request, user=None)
            models = {model['id']: model for model in base_models}
            # Update request.app.state.MODELS for generate_chat_completion
            request.app.state.MODELS = models
            request.app.state.BASE_MODELS = base_models
        except Exception as e:
            log.error(f"Failed to load models: {e}")
            models = {}
        
        # Get default model from available models
        default_model_id = None
        if models:
            # Try to get the first available model
            default_model_id = list(models.keys())[0]
        
        # Fallback if no models available
        if not default_model_id:
            log.error("No models available for chat summarization")
            return None

        task_model_id = get_task_model_id(
            default_model_id,
            TASK_MODEL,
            TASK_MODEL_EXTERNAL,
            models,
        )

        # Prepare the prompt
        prompt = CHAT_SUMMARIZATION_PROMPT.format(chat_history=chat_history)

        # Call the LLM
        from open_webui.utils.chat import generate_chat_completion
        from open_webui.models.users import Users

        # Get user object for the API call
        user = Users.get_user_by_id(user_id)
        if not user:
            log.error(f"User {user_id} not found")
            return None

        payload = {
            'model': task_model_id,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            'max_completion_tokens': 2000,
        }

        response = await generate_chat_completion(request, form_data=payload, user=user)

        # Parse the response
        if hasattr(response, 'body'):
            # Handle StreamingResponse
            body = await response.body.read()
            content = json.loads(body.decode())
        else:
            content = response

        # Extract the generated text
        if isinstance(content, dict):
            if 'choices' in content and len(content['choices']) > 0:
                generated_text = content['choices'][0].get('message', {}).get('content', '')
            elif 'content' in content:
                generated_text = content['content']
            else:
                generated_text = str(content)
        else:
            generated_text = str(content)

        # Parse JSON from the response
        result = parse_summary_response(generated_text)

        if result:
            result['chat_id'] = chat_id
            result['user_id'] = user_id
            result['message_count'] = len(messages)
            log.info(f"Successfully generated summary for chat {chat_id}")
            return result

        return None

    except Exception as e:
        log.exception(f"Error generating summary for chat {chat_id}: {e}")
        return None


def extract_messages_from_chat(chat_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract messages from chat in chronological order."""
    messages = []
    
    # Структура чата: chat.chat.history.messages
    # chat_data приходит как chat.chat (весь объект чата)
    history = chat_data.get('history', {})
    msg_dict = history.get('messages', {})
    current_id = history.get('currentId')
    
    log.debug(f"Extracting messages: history keys={list(history.keys()) if history else 'None'}, msg_count={len(msg_dict)}, current_id={current_id}")
    
    if not msg_dict or not current_id:
        log.warning(f"Empty chat or missing currentId: msg_dict={bool(msg_dict)}, current_id={current_id}")
        return []
    
    # Build message chain backwards from currentId
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
    
    # Extract content
    for msg in msg_chain:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        # Handle different content formats
        if isinstance(content, list):
            # New format: [{"type": "text", "text": "..."}, ...]
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
            content = ' '.join(text_parts)
        elif isinstance(content, dict):
            # Sometimes content is {"text": "..."}
            content = content.get('text', str(content))
        elif not isinstance(content, str):
            content = str(content)
        
        if content.strip() and role in ('user', 'assistant'):
            messages.append({
                'role': role,
                'content': content.strip(),
            })
    
    return messages


def format_chat_history(messages: List[Dict[str, str]], max_length: int = 8000) -> str:
    """Format messages into a string for the prompt."""
    lines = []

    for msg in messages:
        role = msg['role']
        content = msg['content']

        if role == 'user':
            lines.append(f"Пользователь: {content}")
        elif role == 'assistant':
            lines.append(f"Ассистент: {content}")

    result = '\n\n'.join(lines)

    # Truncate if too long
    if len(result) > max_length:
        # Keep beginning and end
        half = max_length // 2
        result = result[:half] + '\n\n...[пропущено]...\n\n' + result[-half:]

    return result


def parse_summary_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from LLM response, handling various formats."""
    try:
        # Try to find JSON in the response
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]

        if text.endswith('```'):
            text = text[:-3]

        text = text.strip()

        # Try to parse as JSON
        data = json.loads(text)

        # Validate required fields
        if 'summary' not in data:
            data['summary'] = 'Нет описания'

        if 'category' not in data:
            data['category'] = 'general'

        if 'tags' not in data:
            data['tags'] = []

        if 'insights' not in data:
            data['insights'] = []

        # Filter out SKIP insights and validate
        valid_insights = []
        for insight in data['insights']:
            if isinstance(insight, dict):
                insight_type = insight.get('type', 'SKIP')
                if insight_type != 'SKIP' and 'content' in insight:
                    valid_insights.append({
                        'type': insight_type,
                        'content': insight['content'],
                        'importance': float(insight.get('importance', 0.5)),
                    })

        data['insights'] = valid_insights

        # Calculate importance score based on insights
        if valid_insights:
            avg_importance = sum(i['importance'] for i in valid_insights) / len(valid_insights)
            data['importance_score'] = avg_importance
        else:
            data['importance_score'] = 0.3

        return data

    except json.JSONDecodeError as e:
        log.error(f"Failed to parse JSON from response: {e}")
        log.debug(f"Response text: {text[:500]}...")
        return None
    except Exception as e:
        log.exception(f"Error parsing summary response: {e}")
        return None


async def save_chat_summary_with_vectors(
    request,
    summary_data: Dict[str, Any],
) -> Optional[str]:
    """Save chat summary to DB and create vector embedding."""
    try:
        chat_id = summary_data['chat_id']
        user_id = summary_data['user_id']

        # Determine TTL based on category and importance
        category = summary_data.get('category', 'general')
        importance = summary_data.get('importance_score', 0.5)

        if category == 'PROJECT_CONTEXT':
            ttl_days = 90
        elif importance > 0.8:
            ttl_days = 60
        else:
            ttl_days = 30

        # Save to database
        summary_record = ChatSummaries.insert_new_summary(
            chat_id=chat_id,
            user_id=user_id,
            summary=summary_data['summary'],
            insights=summary_data['insights'],
            category=category,
            tags=summary_data.get('tags', []),
            importance_score=importance,
            message_count=summary_data.get('message_count', 0),
            ttl_days=ttl_days,
        )

        if not summary_record:
            log.error(f"Failed to save summary for chat {chat_id}")
            return None

        # Create vector embedding
        # Combine summary and insights for better searchability
        content_for_embedding = summary_data['summary'] + '\n\n'
        for insight in summary_data['insights']:
            content_for_embedding += f"{insight['type']}: {insight['content']}\n"

        # Generate embedding
        vector = await request.app.state.EMBEDDING_FUNCTION(
            content_for_embedding,
            user={'id': user_id},
        )

        # Store in vector DB
        collection_name = f'user-chat-summaries-{user_id}'

        VECTOR_DB_CLIENT.upsert(
            collection_name=collection_name,
            items=[
                {
                    'id': summary_record.id,
                    'text': content_for_embedding,
                    'vector': vector,
                    'metadata': {
                        'chat_id': chat_id,
                        'category': category,
                        'tags': summary_data.get('tags', []),
                        'importance_score': importance,
                        'created_at': summary_record.created_at,
                        'expires_at': summary_record.expires_at,
                    },
                }
            ],
        )

        log.info(f"Saved summary {summary_record.id} for chat {chat_id} with vectors")
        return summary_record.id

    except Exception as e:
        log.exception(f"Error saving chat summary with vectors: {e}")
        return None


async def process_user_preference_insights(
    request,
    summary_data: Dict[str, Any],
) -> int:
    """Save USER_PREFERENCE insights to standard Memory system.

    Returns number of saved insights.
    """
    saved_count = 0
    user_id = summary_data['user_id']

    for insight in summary_data.get('insights', []):
        if insight.get('type') == 'USER_PREFERENCE':
            try:
                content = insight['content']

                # Add to standard memory system
                from open_webui.routers.memories import AddMemoryForm, add_memory
                from open_webui.models.users import UserModel

                user = UserModel(**{'id': user_id})

                await add_memory(
                    request,
                    AddMemoryForm(content=content),
                    user,
                )

                saved_count += 1
                log.info(f"Saved user preference to memory: {content[:100]}...")

            except Exception as e:
                log.error(f"Error saving preference insight: {e}")

    return saved_count


async def process_pending_chats(
    request,
    older_than_hours: int = 4,
    min_messages: int = 3,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Process all pending chats and generate summaries.

    This is the main entry point for the background task.
    """
    results = {
        'processed': 0,
        'summaries_created': 0,
        'insights_saved': 0,
        'errors': 0,
    }

    try:
        # Get chats that need summarization
        pending_chats = ChatSummaries.get_pending_chats_for_summarization(
            user_id=user_id,
            older_than_hours=older_than_hours,
            min_messages=min_messages,
        )

        log.info(f"Found {len(pending_chats)} chats pending summarization")

        for chat_info in pending_chats:
            try:
                chat_id = chat_info['id']
                chat_user_id = chat_info['user_id']

                # Generate summary
                summary_data = await generate_chat_summary(
                    request,
                    chat_id=chat_id,
                    user_id=chat_user_id,
                )

                if not summary_data:
                    results['errors'] += 1
                    continue

                # Save summary with vectors
                summary_id = await save_chat_summary_with_vectors(request, summary_data)

                if summary_id:
                    results['summaries_created'] += 1

                    # Save USER_PREFERENCE insights to standard memory
                    preferences_saved = await process_user_preference_insights(
                        request, summary_data
                    )
                    results['insights_saved'] += preferences_saved

                results['processed'] += 1

            except Exception as e:
                log.exception(f"Error processing chat {chat_info.get('id')}: {e}")
                results['errors'] += 1

        # Cleanup expired summaries
        expired_count = ChatSummaries.cleanup_expired_summaries()
        if expired_count > 0:
            log.info(f"Cleaned up {expired_count} expired summaries")

        return results

    except Exception as e:
        log.exception(f"Error in process_pending_chats: {e}")
        return results
