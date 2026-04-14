import logging
import time
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, Float, JSON, Index

log = logging.getLogger(__name__)

####################
# Chat Summary DB Schema
# Compressed memories from past conversations,
# holding what matters for future context.
####################


class ChatSummary(Base):
    __tablename__ = 'chat_summary'

    id = Column(String, primary_key=True, unique=True)
    chat_id = Column(String, index=True)  # Reference to chat.id
    user_id = Column(String, index=True)

    # Compressed content
    summary = Column(Text)  # Brief description of the chat
    insights = Column(JSON)  # List of extracted insights

    # Categorization
    category = Column(String, index=True)  # coding_1c, docker, general, etc.
    tags = Column(JSON)  # ["1c", "epf", "debugging"]

    # Metadata
    importance_score = Column(Float, default=0.5)  # 0-1 relevance score
    message_count = Column(BigInteger, default=0)  # Number of messages in original chat
    created_at = Column(BigInteger)
    expires_at = Column(BigInteger)  # TTL for auto-cleanup

    __table_args__ = (
        # Index for finding summaries by user + expiration (for cleanup)
        Index('user_id_expires_at_idx', 'user_id', 'expires_at'),
        # Index for finding summaries by chat_id
        Index('chat_id_idx', 'chat_id'),
    )


class ChatSummaryModel(BaseModel):
    id: str
    chat_id: str
    user_id: str
    summary: str
    insights: List[Dict[str, Any]]
    category: str
    tags: List[str]
    importance_score: float
    message_count: int
    created_at: int
    expires_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Chat Summaries Table
####################


class ChatSummariesTable:
    def insert_new_summary(
        self,
        chat_id: str,
        user_id: str,
        summary: str,
        insights: List[Dict[str, Any]],
        category: str = "general",
        tags: List[str] = None,
        importance_score: float = 0.5,
        message_count: int = 0,
        ttl_days: int = 30,
        db: Optional[Session] = None,
    ) -> Optional[ChatSummaryModel]:
        """Create a new chat summary with TTL."""
        with get_db_context(db) as db:
            id = str(uuid.uuid4())
            now = int(time.time())
            expires_at = now + (ttl_days * 24 * 60 * 60)

            summary_data = ChatSummaryModel(
                id=id,
                chat_id=chat_id,
                user_id=user_id,
                summary=summary,
                insights=insights or [],
                category=category,
                tags=tags or [],
                importance_score=importance_score,
                message_count=message_count,
                created_at=now,
                expires_at=expires_at,
            )

            result = ChatSummary(**summary_data.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)

            if result:
                return ChatSummaryModel.model_validate(result)
            return None

    def get_summary_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ChatSummaryModel]:
        """Get summary for a specific chat."""
        with get_db_context(db) as db:
            try:
                summary = db.query(ChatSummary).filter_by(chat_id=chat_id).first()
                if summary:
                    return ChatSummaryModel.model_validate(summary)
                return None
            except Exception:
                return None

    def get_summaries_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[ChatSummaryModel]:
        """Get all summaries for a user, optionally filtered by category."""
        with get_db_context(db) as db:
            try:
                query = db.query(ChatSummary).filter_by(user_id=user_id)

                if category:
                    query = query.filter_by(category=category)

                summaries = query.order_by(ChatSummary.created_at.desc()).offset(skip).limit(limit).all()
                return [ChatSummaryModel.model_validate(s) for s in summaries]
            except Exception:
                return []

    def get_pending_chats_for_summarization(
        self,
        user_id: Optional[str] = None,
        older_than_hours: int = 1,
        min_messages: int = 2,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Get chats that need summarization."""
        with get_db_context(db) as db:
            try:
                from open_webui.models.chats import Chat

                cutoff_time = int(time.time()) - (older_than_hours * 60 * 60)
                now = int(time.time())

                log.info(f"[DEBUG] Looking for chats older than {older_than_hours}h (cutoff: {cutoff_time}, now: {now})")
                log.info(f"[DEBUG] User filter: {user_id}")

                # First, count all chats
                total_chats = db.query(Chat).count()
                log.info(f"[DEBUG] Total chats in DB: {total_chats}")

                # Count chats with summaries
                summarized_count = db.query(ChatSummary).count()
                log.info(f"[DEBUG] Chats with summaries: {summarized_count}")

                # Get chat IDs with existing summaries
                summarized_chat_ids = db.query(ChatSummary.chat_id).scalar_subquery()

                # Query: chats without summaries, older than cutoff
                query = db.query(Chat).filter(
                    Chat.updated_at < cutoff_time,
                    ~Chat.id.in_(summarized_chat_ids)
                )

                if user_id:
                    query = query.filter_by(user_id=user_id)

                # Log the SQL query for debugging
                log.info(f"[DEBUG] SQL Query: {query}")

                chats = query.all()
                log.info(f"[DEBUG] Found {len(chats)} chats matching time criteria")

                # Filter by message count
                result = []
                for chat in chats:
                    # Get messages from chat.chat (structure: chat.chat.history.messages)
                    chat_data = chat.chat or {}
                    messages_dict = chat_data.get('history', {}).get('messages', {})
                    message_count = len(messages_dict)
                    
                    # Count real messages (user + assistant)
                    real_messages = sum(
                        1 for msg in messages_dict.values()
                        if isinstance(msg, dict) and msg.get('role') in ('user', 'assistant')
                    )
                    
                    log.info(f"[DEBUG] Chat {chat.id[:8]}...: updated_at={chat.updated_at}, total_msgs={message_count}, real_msgs={real_messages}")
                    
                    if real_messages >= min_messages:
                        result.append({
                            'id': chat.id,
                            'user_id': chat.user_id,
                            'title': chat.title,
                            'updated_at': chat.updated_at,
                            'message_count': real_messages,
                        })

                log.info(f"[DEBUG] Returning {len(result)} chats after message count filter")
                return result
                
            except Exception as e:
                log.exception(f"Error getting pending chats: {e}")
                return []

    def delete_summary_by_id(
        self,
        summary_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Delete a summary by ID."""
        with get_db_context(db) as db:
            try:
                summary = db.get(ChatSummary, summary_id)
                if summary:
                    db.delete(summary)
                    db.commit()
                    return True
                return False
            except Exception:
                return False

    def delete_summaries_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Delete all summaries for a chat."""
        with get_db_context(db) as db:
            try:
                db.query(ChatSummary).filter_by(chat_id=chat_id).delete()
                db.commit()
                return True
            except Exception:
                return False

    def cleanup_expired_summaries(
        self,
        db: Optional[Session] = None,
    ) -> int:
        """Delete summaries that have exceeded their TTL.

        Returns number of deleted records.
        """
        with get_db_context(db) as db:
            try:
                now = int(time.time())
                result = db.query(ChatSummary).filter(ChatSummary.expires_at < now).delete()
                db.commit()
                return result
            except Exception:
                return 0

    def update_summary_ttl(
        self,
        summary_id: str,
        new_ttl_days: int,
        db: Optional[Session] = None,
    ) -> Optional[ChatSummaryModel]:
        """Update the TTL of a summary (extend expiration)."""
        with get_db_context(db) as db:
            try:
                summary = db.get(ChatSummary, summary_id)
                if not summary:
                    return None

                now = int(time.time())
                summary.expires_at = now + (new_ttl_days * 24 * 60 * 60)
                summary.created_at = now  # Reset creation time

                db.commit()
                db.refresh(summary)
                return ChatSummaryModel.model_validate(summary)
            except Exception:
                return None


ChatSummaries = ChatSummariesTable()
