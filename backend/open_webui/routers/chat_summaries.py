from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional, List
import logging

from open_webui.models.chat_summaries import ChatSummaries, ChatSummaryModel
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user
from open_webui.utils.access_control import has_permission
from open_webui.constants import ERROR_MESSAGES
from open_webui.retrieval.vector.factory import VECTOR_DB_CLIENT

log = logging.getLogger(__name__)

router = APIRouter()


############################
# Get Chat Summaries
############################


@router.get('/', response_model=list[ChatSummaryModel])
async def get_chat_summaries(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    user=Depends(get_verified_user),
):
    """Get all chat summaries for the current user."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    summaries = ChatSummaries.get_summaries_by_user_id(
        user_id=user.id,
        skip=skip,
        limit=limit,
        category=category,
    )

    return summaries


############################
# Get Chat Summary by Chat ID
############################


@router.get('/chat/{chat_id}', response_model=Optional[ChatSummaryModel])
async def get_chat_summary_by_chat_id(
    chat_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get summary for a specific chat."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    summary = ChatSummaries.get_summary_by_chat_id(chat_id)

    if not summary:
        raise HTTPException(status_code=404, detail='Summary not found')

    if summary.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    return summary


############################
# Search Chat Summaries (Vector Search)
############################


class SearchSummariesForm(BaseModel):
    query: str
    k: Optional[int] = 5
    category: Optional[str] = None


@router.post('/search')
async def search_chat_summaries(
    request: Request,
    form_data: SearchSummariesForm,
    user=Depends(get_verified_user),
):
    """Search chat summaries using vector similarity."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    try:
        # Generate embedding for the query
        vector = await request.app.state.EMBEDDING_FUNCTION(
            form_data.query,
            user=user,
        )

        # Search in vector DB
        collection_name = f'user-chat-summaries-{user.id}'

        results = VECTOR_DB_CLIENT.search(
            collection_name=collection_name,
            vectors=[vector],
            limit=form_data.k,
        )

        # Format results
        summaries = []
        if results and hasattr(results, 'documents') and results.documents:
            for idx, doc in enumerate(results.documents[0]):
                metadata = results.metadatas[0][idx] if results.metadatas else {}

                # Filter by category if specified
                if form_data.category and metadata.get('category') != form_data.category:
                    continue

                summaries.append({
                    'id': results.ids[0][idx] if results.ids else None,
                    'content': doc,
                    'metadata': metadata,
                })

        return {'summaries': summaries}

    except Exception as e:
        log.exception(f'Error searching chat summaries: {e}')
        raise HTTPException(status_code=500, detail=str(e))


############################
# Delete Chat Summary
############################


@router.delete('/{summary_id}', response_model=bool)
async def delete_chat_summary(
    summary_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete a chat summary."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    # Get summary to check ownership
    from open_webui.internal.db import get_session

    with get_session() as db:
        summary = db.get(ChatSummaries.ChatSummary, summary_id)

        if not summary:
            raise HTTPException(status_code=404, detail='Summary not found')

        if summary.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
            )

        # Delete from vector DB
        try:
            collection_name = f'user-chat-summaries-{user.id}'
            VECTOR_DB_CLIENT.delete(
                collection_name=collection_name,
                ids=[summary_id],
            )
        except Exception as e:
            log.error(f'Error deleting from vector DB: {e}')

        # Delete from SQL DB
        result = ChatSummaries.delete_summary_by_id(summary_id)

        return result


############################
# Trigger Manual Summarization
############################


class TriggerSummarizationForm(BaseModel):
    chat_id: Optional[str] = None  # If None, process all pending chats


@router.post('/trigger', response_model=dict)
async def trigger_summarization(
    request: Request,
    form_data: TriggerSummarizationForm,
    user=Depends(get_verified_user),
):
    """Manually trigger chat summarization."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    try:
        from open_webui.utils.chat_summarizer import (
            generate_chat_summary,
            save_chat_summary_with_vectors,
            process_user_preference_insights,
            process_pending_chats,
        )

        if form_data.chat_id:
            # Process specific chat
            summary_data = await generate_chat_summary(
                request,
                chat_id=form_data.chat_id,
                user_id=user.id,
            )

            if not summary_data:
                return {'status': 'error', 'message': 'Failed to generate summary'}

            summary_id = await save_chat_summary_with_vectors(request, summary_data)

            if summary_id:
                preferences_saved = await process_user_preference_insights(
                    request, summary_data
                )
                return {
                    'status': 'success',
                    'summary_id': summary_id,
                    'insights_saved': preferences_saved,
                }
            else:
                return {'status': 'error', 'message': 'Failed to save summary'}

        else:
            # Process all pending chats
            results = await process_pending_chats(
                request,
                older_than_hours=0,  # Process all
                min_messages=3,
                user_id=user.id,
            )

            return {
                'status': 'success',
                'results': results,
            }

    except Exception as e:
        log.exception(f'Error triggering summarization: {e}')
        raise HTTPException(status_code=500, detail=str(e))


############################
# Cleanup Expired Summaries
############################


@router.post('/cleanup', response_model=dict)
async def cleanup_expired_summaries(
    request: Request,
    user=Depends(get_verified_user),
):
    """Manually trigger cleanup of expired summaries."""
    if not has_permission(user.id, 'features.chat_summaries', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    try:
        # Only admin can cleanup all, regular users cleanup only their own
        if user.role == 'admin':
            # Cleanup all expired summaries
            from open_webui.internal.db import get_session

            with get_session() as db:
                from open_webui.models.chat_summaries import ChatSummary
                import time

                now = int(time.time())
                expired = db.query(ChatSummary).filter(ChatSummary.expires_at < now).all()

                deleted_count = 0
                for summary in expired:
                    # Delete from vector DB
                    try:
                        collection_name = f'user-chat-summaries-{summary.user_id}'
                        VECTOR_DB_CLIENT.delete(
                            collection_name=collection_name,
                            ids=[summary.id],
                        )
                    except Exception as e:
                        log.error(f'Error deleting from vector DB: {e}')

                    # Delete from SQL DB
                    db.delete(summary)
                    deleted_count += 1

                db.commit()

                return {
                    'status': 'success',
                    'deleted_count': deleted_count,
                }
        else:
            # Regular user - cleanup only their summaries
            count = ChatSummaries.cleanup_expired_summaries()
            return {
                'status': 'success',
                'deleted_count': count,
            }

    except Exception as e:
        log.exception(f'Error cleaning up summaries: {e}')
        raise HTTPException(status_code=500, detail=str(e))
