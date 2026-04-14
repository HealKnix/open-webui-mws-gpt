import logging
import time
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context, JSONField
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
    Text,
    Integer,
    Index,
)

log = logging.getLogger(__name__)

####################
# Chat Context Segment DB Schema
# Rolling compression of chat context with chain-based summaries.
# Each segment represents a compressed portion of the conversation.
####################


class ChatContextSegment(Base):
    __tablename__ = 'chat_context_segment'

    # Identity
    id = Column(String, primary_key=True, unique=True)
    chat_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)

    # Chain structure (for rollback support)
    parent_segment_id = Column(String, ForeignKey('chat_context_segment.id', ondelete='SET NULL'), nullable=True)

    # Message range covered by this segment
    from_message_id = Column(String, nullable=False)
    to_message_id = Column(String, nullable=False)

    # Compressed content
    summary_text = Column(Text, nullable=False)  # Human-readable summary
    summary_json = Column(JSONField, nullable=False)  # Structured: {short_summary, facts[], decisions[], open_questions[]}
    tool_digest_json = Column(JSONField, nullable=True)  # Tool calls summary

    # Token statistics
    token_count_before = Column(Integer, default=0)  # Tokens before compression
    token_count_after = Column(Integer, default=0)   # Tokens after compression

    # Status management
    status = Column(String, default='active')  # active | superseded | failed
    version = Column(Integer, default=1)  # Incremented on each compaction

    # Timestamps
    created_at = Column(BigInteger, nullable=False)
    expires_at = Column(BigInteger, nullable=True)  # For auto-cleanup

    __table_args__ = (
        # Index for getting segments by chat (ordered by creation time)
        Index('idx_chat_context_segment_chat_created', 'chat_id', 'created_at'),
        # Index for getting active segments
        Index('idx_chat_context_segment_chat_status', 'chat_id', 'status'),
        # Index for cleanup job
        Index('idx_chat_context_segment_expires', 'expires_at'),
        # Index for chain traversal
        Index('idx_chat_context_segment_parent', 'parent_segment_id'),
    )


####################
# Pydantic Models
####################


class SummaryJson(BaseModel):
    """Structured summary content."""
    short_summary: str
    facts: List[str] = []
    decisions: List[str] = []
    open_questions: List[str] = []


class ToolDigestItem(BaseModel):
    """Single tool call digest."""
    tool_name: str
    arguments_summary: str
    result_summary: str
    status: str  # success | error
    artifacts: List[str] = []


class ChatContextSegmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chat_id: str
    user_id: str
    parent_segment_id: Optional[str] = None
    from_message_id: str
    to_message_id: str
    summary_text: str
    summary_json: Dict[str, Any]  # SummaryJson as dict
    tool_digest_json: Optional[List[Dict[str, Any]]] = None  # List[ToolDigestItem] as dict
    token_count_before: int
    token_count_after: int
    status: str
    version: int
    created_at: int
    expires_at: Optional[int] = None


####################
# Table Operations
####################


class ChatContextSegmentsTable:
    def insert_new_segment(
        self,
        chat_id: str,
        user_id: str,
        from_message_id: str,
        to_message_id: str,
        summary_text: str,
        summary_json: Dict[str, Any],
        tool_digest_json: Optional[List[Dict[str, Any]]] = None,
        token_count_before: int = 0,
        token_count_after: int = 0,
        parent_segment_id: Optional[str] = None,
        ttl_days: int = 30,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextSegmentModel]:
        """Create a new context segment with TTL."""
        with get_db_context(db) as db:
            id = str(uuid.uuid4())
            now = int(time.time())
            expires_at = now + (ttl_days * 24 * 60 * 60)

            # Determine version
            version = 1
            if parent_segment_id:
                parent = db.get(ChatContextSegment, parent_segment_id)
                if parent:
                    version = parent.version + 1

            segment_data = ChatContextSegmentModel(
                id=id,
                chat_id=chat_id,
                user_id=user_id,
                parent_segment_id=parent_segment_id,
                from_message_id=from_message_id,
                to_message_id=to_message_id,
                summary_text=summary_text,
                summary_json=summary_json,
                tool_digest_json=tool_digest_json,
                token_count_before=token_count_before,
                token_count_after=token_count_after,
                status='active',
                version=version,
                created_at=now,
                expires_at=expires_at,
            )

            result = ChatContextSegment(**segment_data.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)

            if result:
                return ChatContextSegmentModel.model_validate(result)
            return None

    def get_segment_by_id(
        self,
        segment_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextSegmentModel]:
        """Get a segment by ID."""
        with get_db_context(db) as db:
            segment = db.get(ChatContextSegment, segment_id)
            if segment:
                return ChatContextSegmentModel.model_validate(segment)
            return None

    def get_segments_by_chat_id(
        self,
        chat_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        db: Optional[Session] = None,
    ) -> List[ChatContextSegmentModel]:
        """Get all segments for a chat, optionally filtered by status."""
        with get_db_context(db) as db:
            query = db.query(ChatContextSegment).filter_by(chat_id=chat_id)

            if status:
                query = query.filter_by(status=status)

            segments = (
                query.order_by(ChatContextSegment.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [ChatContextSegmentModel.model_validate(s) for s in segments]

    def get_active_segment_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextSegmentModel]:
        """Get the currently active segment for a chat."""
        with get_db_context(db) as db:
            segment = (
                db.query(ChatContextSegment)
                .filter_by(chat_id=chat_id, status='active')
                .order_by(ChatContextSegment.created_at.desc())
                .first()
            )
            if segment:
                return ChatContextSegmentModel.model_validate(segment)
            return None

    def supersede_segment(
        self,
        segment_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Mark a segment as superseded (when creating a new one)."""
        with get_db_context(db) as db:
            segment = db.get(ChatContextSegment, segment_id)
            if segment:
                segment.status = 'superseded'
                db.commit()
                return True
            return False

    def mark_segment_failed(
        self,
        segment_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Mark a segment as failed."""
        with get_db_context(db) as db:
            segment = db.get(ChatContextSegment, segment_id)
            if segment:
                segment.status = 'failed'
                db.commit()
                return True
            return False

    def delete_segment_by_id(
        self,
        segment_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Delete a segment by ID."""
        with get_db_context(db) as db:
            segment = db.get(ChatContextSegment, segment_id)
            if segment:
                db.delete(segment)
                db.commit()
                return True
            return False

    def delete_segments_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> int:
        """Delete all segments for a chat. Returns count deleted."""
        with get_db_context(db) as db:
            count = db.query(ChatContextSegment).filter_by(chat_id=chat_id).delete()
            db.commit()
            return count

    def cleanup_expired_segments(
        self,
        db: Optional[Session] = None,
    ) -> int:
        """Delete segments that have exceeded their TTL.

        Returns number of deleted records.
        """
        with get_db_context(db) as db:
            now = int(time.time())
            result = db.query(ChatContextSegment).filter(
                ChatContextSegment.expires_at < now
            ).delete()
            db.commit()
            return result

    def cleanup_old_segments_by_chat(
        self,
        chat_id: str,
        keep_count: int = 10,
        db: Optional[Session] = None,
    ) -> int:
        """Keep only the most recent N segments for a chat.

        Returns number of deleted records.
        """
        with get_db_context(db) as db:
            # Get segments to delete (older than keep_count)
            segments_to_delete = (
                db.query(ChatContextSegment)
                .filter_by(chat_id=chat_id)
                .order_by(ChatContextSegment.created_at.desc())
                .offset(keep_count)
                .all()
            )

            count = 0
            for segment in segments_to_delete:
                db.delete(segment)
                count += 1

            if count > 0:
                db.commit()

            return count

    def get_segment_chain(
        self,
        segment_id: str,
        db: Optional[Session] = None,
    ) -> List[ChatContextSegmentModel]:
        """Get the chain of segments from the given segment back to the root.

        Returns list from oldest to newest.
        """
        with get_db_context(db) as db:
            chain = []
            current_id = segment_id
            visited = set()

            while current_id and current_id not in visited:
                visited.add(current_id)
                segment = db.get(ChatContextSegment, current_id)
                if not segment:
                    break

                chain.append(ChatContextSegmentModel.model_validate(segment))
                current_id = segment.parent_segment_id

            # Reverse to get oldest first
            chain.reverse()
            return chain

    def update_segment_ttl(
        self,
        segment_id: str,
        new_ttl_days: int,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextSegmentModel]:
        """Update the TTL of a segment (extend expiration)."""
        with get_db_context(db) as db:
            segment = db.get(ChatContextSegment, segment_id)
            if not segment:
                return None

            now = int(time.time())
            segment.expires_at = now + (new_ttl_days * 24 * 60 * 60)

            db.commit()
            db.refresh(segment)
            return ChatContextSegmentModel.model_validate(segment)


ChatContextSegments = ChatContextSegmentsTable()
