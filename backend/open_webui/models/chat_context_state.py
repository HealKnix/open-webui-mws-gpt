import logging
import time
from typing import Optional

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Integer,
    Boolean,
)

log = logging.getLogger(__name__)

####################
# Chat Context State DB Schema
# Stores the current compaction state and settings for each chat.
####################


class ChatContextState(Base):
    __tablename__ = 'chat_context_state'

    # Primary key - one state per chat
    chat_id = Column(String, primary_key=True, unique=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)

    # Current compaction position
    last_compacted_message_id = Column(String, nullable=True)
    active_segment_id = Column(String, nullable=True)

    # Thresholds for automatic compaction
    threshold_messages = Column(Integer, default=20)  # Min messages to trigger compaction
    keep_last_messages = Column(Integer, default=5)   # Raw messages to keep after compaction
    threshold_tokens = Column(Integer, default=4000)  # Min tokens to trigger compaction

    # Feature toggles
    enabled = Column(Boolean, default=True)           # Master toggle for this chat
    include_tool_data = Column(Boolean, default=True) # Include tool digest in summary

    # Cleanup settings
    max_segment_age_days = Column(Integer, default=30)   # Auto-delete segments older than N days
    max_segments_per_chat = Column(Integer, default=10)  # Keep only N most recent segments

    # Timestamps
    updated_at = Column(BigInteger, nullable=False)


####################
# Pydantic Models
####################


class ChatContextStateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: str
    user_id: str
    last_compacted_message_id: Optional[str] = None
    active_segment_id: Optional[str] = None
    threshold_messages: int = 10
    keep_last_messages: int = 4
    threshold_tokens: int = 4000
    enabled: bool = True
    include_tool_data: bool = True
    max_segment_age_days: int = 30
    max_segments_per_chat: int = 10
    updated_at: int


class ChatContextSettingsForm(BaseModel):
    """Form for updating context compression settings."""
    enabled: Optional[bool] = None
    threshold_messages: Optional[int] = None
    keep_last_messages: Optional[int] = None
    threshold_tokens: Optional[int] = None
    include_tool_data: Optional[bool] = None
    max_segment_age_days: Optional[int] = None
    max_segments_per_chat: Optional[int] = None


####################
# Table Operations
####################


class ChatContextStateTable:
    # Default settings
    DEFAULT_THRESHOLD_MESSAGES = 20
    DEFAULT_KEEP_LAST_MESSAGES = 5
    DEFAULT_THRESHOLD_TOKENS = 4000
    DEFAULT_MAX_SEGMENT_AGE_DAYS = 30
    DEFAULT_MAX_SEGMENTS_PER_CHAT = 10

    def get_or_create_state(
        self,
        chat_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> ChatContextStateModel:
        """Get existing state or create with defaults."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)

            if state:
                return ChatContextStateModel.model_validate(state)

            # Create new state with defaults
            now = int(time.time())
            new_state = ChatContextState(
                chat_id=chat_id,
                user_id=user_id,
                last_compacted_message_id=None,
                active_segment_id=None,
                threshold_messages=self.DEFAULT_THRESHOLD_MESSAGES,
                keep_last_messages=self.DEFAULT_KEEP_LAST_MESSAGES,
                threshold_tokens=self.DEFAULT_THRESHOLD_TOKENS,
                enabled=True,
                include_tool_data=True,
                max_segment_age_days=self.DEFAULT_MAX_SEGMENT_AGE_DAYS,
                max_segments_per_chat=self.DEFAULT_MAX_SEGMENTS_PER_CHAT,
                updated_at=now,
            )

            db.add(new_state)
            db.commit()
            db.refresh(new_state)

            return ChatContextStateModel.model_validate(new_state)

    def get_state_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextStateModel]:
        """Get state for a chat (returns None if not exists)."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if state:
                return ChatContextStateModel.model_validate(state)
            return None

    def update_state(
        self,
        chat_id: str,
        last_compacted_message_id: Optional[str] = None,
        active_segment_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextStateModel]:
        """Update compaction state after successful compaction."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if not state:
                return None

            if last_compacted_message_id is not None:
                state.last_compacted_message_id = last_compacted_message_id

            if active_segment_id is not None:
                state.active_segment_id = active_segment_id

            state.updated_at = int(time.time())

            db.commit()
            db.refresh(state)
            return ChatContextStateModel.model_validate(state)

    def update_settings(
        self,
        chat_id: str,
        form_data: ChatContextSettingsForm,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextStateModel]:
        """Update settings for a chat."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if not state:
                return None

            # Update only provided fields
            if form_data.enabled is not None:
                state.enabled = form_data.enabled

            if form_data.threshold_messages is not None:
                state.threshold_messages = max(5, form_data.threshold_messages)

            if form_data.keep_last_messages is not None:
                state.keep_last_messages = max(1, form_data.keep_last_messages)

            if form_data.threshold_tokens is not None:
                state.threshold_tokens = max(1000, form_data.threshold_tokens)

            if form_data.include_tool_data is not None:
                state.include_tool_data = form_data.include_tool_data

            if form_data.max_segment_age_days is not None:
                state.max_segment_age_days = max(1, form_data.max_segment_age_days)

            if form_data.max_segments_per_chat is not None:
                state.max_segments_per_chat = max(1, form_data.max_segments_per_chat)

            state.updated_at = int(time.time())

            db.commit()
            db.refresh(state)
            return ChatContextStateModel.model_validate(state)

    def delete_state_by_chat_id(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Delete state for a chat (e.g., when chat is deleted)."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if state:
                db.delete(state)
                db.commit()
                return True
            return False

    def is_compaction_enabled(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Check if compaction is enabled for a chat."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if state:
                return state.enabled
            return True  # Default to enabled if no state exists

    def should_compact(
        self,
        chat_id: str,
        message_count: int,
        token_count: int,
        db: Optional[Session] = None,
    ) -> bool:
        """Check if compaction should be triggered based on thresholds."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if not state:
                # Use defaults if no state exists
                return (
                    message_count >= self.DEFAULT_THRESHOLD_MESSAGES or
                    token_count >= self.DEFAULT_THRESHOLD_TOKENS
                )

            if not state.enabled:
                return False

            return (
                message_count >= state.threshold_messages or
                token_count >= state.threshold_tokens
            )

    def get_all_enabled_states(
        self,
        skip: int = 0,
        limit: int = 1000,
        db: Optional[Session] = None,
    ) -> list[ChatContextStateModel]:
        """Get all chats with compaction enabled (for background jobs)."""
        with get_db_context(db) as db:
            states = (
                db.query(ChatContextState)
                .filter_by(enabled=True)
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [ChatContextStateModel.model_validate(s) for s in states]

    def reset_state(
        self,
        chat_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ChatContextStateModel]:
        """Reset compaction state (e.g., for rollback)."""
        with get_db_context(db) as db:
            state = db.get(ChatContextState, chat_id)
            if not state:
                return None

            state.last_compacted_message_id = None
            state.active_segment_id = None
            state.updated_at = int(time.time())

            db.commit()
            db.refresh(state)
            return ChatContextStateModel.model_validate(state)


ChatContextStates = ChatContextStateTable()
