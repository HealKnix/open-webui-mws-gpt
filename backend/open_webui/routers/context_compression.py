"""
Context Compression Router

API endpoints for managing chat context compression.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional, List
import logging

from open_webui.models.chat_context_segments import (
    ChatContextSegments,
    ChatContextSegmentModel,
)
from open_webui.models.chat_context_state import (
    ChatContextStates,
    ChatContextStateModel,
    ChatContextSettingsForm,
)
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user
from open_webui.utils.access_control import has_permission
from open_webui.utils.context_compactor import compact_chat_context
from open_webui.utils.context_builder import build_chat_context
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)

router = APIRouter()


############################
# Get Context State
############################


@router.get('/state', response_model=ChatContextStateModel)
async def get_context_state(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get context compression state for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    state = ChatContextStates.get_or_create_state(chat_id, user.id)
    return state


############################
# Update Settings
############################


@router.put('/settings', response_model=ChatContextStateModel)
async def update_context_settings(
    chat_id: str,
    form_data: ChatContextSettingsForm,
    request: Request,
    user=Depends(get_verified_user),
):
    """Update context compression settings for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    updated_state = ChatContextStates.update_settings(chat_id, form_data)
    if not updated_state:
        raise HTTPException(status_code=500, detail='Failed to update settings')

    return updated_state


############################
# Get Segments
############################


@router.get('/segments', response_model=list[ChatContextSegmentModel])
async def get_context_segments(
    chat_id: str,
    request: Request,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user=Depends(get_verified_user),
):
    """Get all context segments for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    segments = ChatContextSegments.get_segments_by_chat_id(
        chat_id=chat_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    return segments


############################
# Get Active Segment
############################


@router.get('/segments/active', response_model=Optional[ChatContextSegmentModel])
async def get_active_segment(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get the currently active segment for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    segment = ChatContextSegments.get_active_segment_by_chat_id(chat_id)
    return segment


############################
# Trigger Compaction
############################


class TriggerCompactionForm(BaseModel):
    force: bool = False  # Force compaction even if thresholds not met


@router.post('/compact', response_model=dict)
async def trigger_compaction(
    chat_id: str,
    form_data: TriggerCompactionForm,
    request: Request,
    user=Depends(get_verified_user),
):
    """Manually trigger context compaction for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    try:
        segment = await compact_chat_context(
            request=request,
            chat_id=chat_id,
            user_id=user.id,
            force=form_data.force,
        )

        if segment:
            return {
                'status': 'success',
                'segment_id': segment.id,
                'token_count_before': segment.token_count_before,
                'token_count_after': segment.token_count_after,
                'messages_compacted': segment.to_message_id,  # Approximate
            }
        else:
            return {
                'status': 'skipped',
                'message': 'Compaction not needed or thresholds not met',
            }

    except Exception as e:
        log.exception(f"Error triggering compaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


############################
# Rollback to Previous Segment
############################


@router.post('/rollback', response_model=dict)
async def rollback_segment(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Rollback to the previous segment (undo last compaction)."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    try:
        # Get current state
        state = ChatContextStates.get_state_by_chat_id(chat_id)
        if not state or not state.active_segment_id:
            raise HTTPException(status_code=400, detail='No active segment to rollback')

        # Get current segment
        current_segment = ChatContextSegments.get_segment_by_id(state.active_segment_id)
        if not current_segment:
            raise HTTPException(status_code=404, detail='Active segment not found')

        # Get parent segment
        if not current_segment.parent_segment_id:
            # No parent, just reset state
            ChatContextStates.reset_state(chat_id)
            ChatContextSegments.delete_segment_by_id(current_segment.id)

            return {
                'status': 'success',
                'message': 'Rolled back to initial state (no compression)',
                'new_active_segment': None,
            }

        parent_segment = ChatContextSegments.get_segment_by_id(
            current_segment.parent_segment_id
        )
        if not parent_segment:
            raise HTTPException(status_code=404, detail='Parent segment not found')

        # Mark current as failed/superseded
        ChatContextSegments.mark_segment_failed(current_segment.id)

        # Reactivate parent
        # Note: We need to update the parent's status back to active
        # This requires a new method or direct DB update
        from open_webui.internal.db import get_session

        with get_session() as db:
            parent = db.get(ChatContextSegments.ChatContextSegment, parent_segment.id)
            if parent:
                parent.status = 'active'
                db.commit()

        # Update state to point to parent
        ChatContextStates.update_state(
            chat_id=chat_id,
            last_compacted_message_id=parent_segment.to_message_id,
            active_segment_id=parent_segment.id,
        )

        return {
            'status': 'success',
            'message': 'Rolled back to previous segment',
            'new_active_segment': parent_segment.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error rolling back segment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


############################
# Get Current Summary
############################


@router.get('/summary', response_model=dict)
async def get_current_summary(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get the current compressed summary for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    # Get active segment
    segment = ChatContextSegments.get_active_segment_by_chat_id(chat_id)
    if not segment:
        return {
            'has_summary': False,
            'message': 'No compressed summary available',
        }

    return {
        'has_summary': True,
        'segment_id': segment.id,
        'summary': segment.summary_json,
        'tool_digest': segment.tool_digest_json,
        'token_count_before': segment.token_count_before,
        'token_count_after': segment.token_count_after,
        'compression_ratio': (
            segment.token_count_before / max(segment.token_count_after, 1)
            if segment.token_count_after > 0
            else 1.0
        ),
        'created_at': segment.created_at,
        'version': segment.version,
    }


############################
# Preview Context
############################


@router.get('/preview', response_model=dict)
async def preview_context(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Preview what context will be sent to LLM (for debugging)."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    try:
        # Build context
        context = build_chat_context(
            chat_id=chat_id,
            user_id=user.id,
            system_prompt=None,  # Don't include system prompt in preview
        )

        # Calculate stats
        total_messages = len(context)
        system_messages = sum(1 for m in context if m.get('role') == 'system')
        user_messages = sum(1 for m in context if m.get('role') == 'user')
        assistant_messages = sum(1 for m in context if m.get('role') == 'assistant')

        # Estimate tokens
        total_chars = sum(len(str(m.get('content', ''))) for m in context)
        estimated_tokens = total_chars // 4

        return {
            'context': context,
            'stats': {
                'total_messages': total_messages,
                'system_messages': system_messages,
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'estimated_tokens': estimated_tokens,
            },
        }

    except Exception as e:
        log.exception(f"Error previewing context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


############################
# Delete All Segments (Reset)
############################


@router.delete('/reset', response_model=dict)
async def reset_compression(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete all segments and reset compression state for a chat."""
    if not has_permission(user.id, 'chat.compression', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Verify chat ownership
    from open_webui.models.chats import Chats

    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail='Chat not found')

    try:
        # Delete all segments
        deleted_count = ChatContextSegments.delete_segments_by_chat_id(chat_id)

        # Reset state
        ChatContextStates.reset_state(chat_id)

        return {
            'status': 'success',
            'deleted_segments': deleted_count,
            'message': 'Compression reset successfully',
        }

    except Exception as e:
        log.exception(f"Error resetting compression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


############################
# Cleanup Expired Segments (Admin only)
############################


@router.post('/cleanup', response_model=dict)
async def cleanup_expired_segments(
    request: Request,
    user=Depends(get_verified_user),
):
    """Cleanup expired segments across all chats (admin only)."""
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    try:
        deleted_count = ChatContextSegments.cleanup_expired_segments()

        return {
            'status': 'success',
            'deleted_segments': deleted_count,
        }

    except Exception as e:
        log.exception(f"Error cleaning up segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))
