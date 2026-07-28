"""
Pydantic models for AI Campus Companion.

Provides data models for authentication, user management, and API request/response
validation. All models use Pydantic v2 for robust data validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================================================================
# Custom Types
# ============================================================================

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        """Validate and convert to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )


# ============================================================================
# Enums
# ============================================================================

class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class OTPPurpose(str, Enum):
    """OTP purpose enumeration."""
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    EMAIL_CHANGE = "email_change"


class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"


# ============================================================================
# Base Models
# ============================================================================

class BaseDBModel(BaseModel):
    """Base model for database documents."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# User Models
# ============================================================================

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserInDB(BaseDBModel, TimestampMixin):
    """User model as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    full_name: str
    password_hash: str
    role: UserRole = UserRole.USER
    is_verified: bool = False
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    companion_progression: list[dict] = Field(default_factory=list)  # list of CompanionProgression dicts

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


# ============================================================================
# OTP Models
# ============================================================================

class OTPBase(BaseModel):
    """Base OTP model."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class OTPVerify(OTPBase):
    """OTP verification request model."""
    purpose: OTPPurpose = OTPPurpose.REGISTRATION


class OTPResend(BaseModel):
    """OTP resend request model."""
    email: EmailStr
    purpose: OTPPurpose = OTPPurpose.REGISTRATION


class OTPInDB(BaseDBModel):
    """OTP model as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    otp: str
    purpose: OTPPurpose
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    attempts: int = 0

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# Token Models
# ============================================================================

class TokenData(BaseModel):
    """Token payload structure."""
    user_id: str
    email: str
    role: UserRole = UserRole.USER
    jti: str  # JWT ID for token revocation
    exp: datetime
    iat: datetime
    type: TokenType = TokenType.ACCESS

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenBlacklist(BaseDBModel):
    """Token blacklist model for revoked tokens."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    token_jti: str = Field(..., unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# Rate Limit Models
# ============================================================================

class RateLimitInDB(BaseDBModel):
    """Rate limit model as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    key: str = Field(..., index=True)
    count: int = 0
    window_start: datetime
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# API Response Models
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
    meta: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[dict] = None


class PaginationMeta(BaseModel):
    """Pagination metadata model."""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(APIResponse):
    """Paginated API response model."""
    meta: PaginationMeta


# ============================================================================
# Companion Progression (embedded in User document)
# ============================================================================

class CompanionProgression(BaseModel):
    """Per-companion progression data stored on the user document."""
    companion_id: str  # backend personality key (e.g. "philosopher")
    xp: int = 0
    level: int = 1
    relationship_points: int = 0
    relationship_stage: str = "Stranger"
    current_episode_id: Optional[str] = None
    episodes_unlocked: list[str] = Field(default_factory=list)
    total_messages: int = 0
    last_interaction: Optional[datetime] = None
    pending_level_up: bool = False


# ============================================================================
# Conversation Session
# ============================================================================

class ConversationSessionInDB(BaseDBModel):
    """Conversation session document stored in MongoDB."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str  # backend personality key
    messages: list[dict] = Field(default_factory=list)  # [{role, content, timestamp}]
    xp_earned: int = 0
    relationship_delta: int = 0
    rl_actions_taken: list[dict] = Field(default_factory=list)
    episode_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# RL Transition
# ============================================================================

class RLTransitionInDB(BaseDBModel):
    """RL transition document for offline training."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    state: dict  # serialized ConversationState
    action: dict  # serialized RLAction {action_type, intensity, topic_focus}
    reward: float
    next_state: dict
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# Companion Memory (separate from legacy memories collection)
# ============================================================================

class CompanionMemoryInDB(BaseDBModel):
    """Companion-specific memory with embedding for semantic search."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    memory_type: str  # "conversation", "story", "feedback", "fact"
    content: str
    metadata: dict = Field(default_factory=dict)
    importance: float = 1.0
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


# ============================================================================
# Chat Request / Response (refactored)
# ============================================================================

class ChatRequestV2(BaseModel):
    """Chat request supporting both trainable and demo companions."""
    companion_key: str = Field(min_length=1, description="Frontend ID (c1-c5) or backend key")
    personality_id: Optional[str] = Field(None, description="Backend personality key (overrides companion_key)")
    message: str = Field(min_length=1, max_length=10_000)
    companion_profile: Optional[dict] = None
    episode_id: Optional[str] = None
    scenario_text: Optional[str] = None


class ChatResponseV2(BaseModel):
    """Chat response with optional progression data."""
    companion: str
    reply: str
    companion_id: str  # resolved backend ID
    tier: str  # "trainable" or "demo"
    xp_delta: Optional[int] = None
    total_xp: Optional[int] = None
    level: Optional[int] = None
    relationship_stage: Optional[str] = None
    rl_action: Optional[str] = None
    pending_level_up: Optional[bool] = None


# ============================================================================
# Story Episode Models
# ============================================================================

class EpisodeNodeChoice(BaseModel):
    """Choice within an episode script node."""
    choice_id: str
    choice_text: str
    next_node_id: Optional[str] = None
    xp_reward: int = 0


class EpisodeScriptNode(BaseModel):
    """Single node in an episode script."""
    node_id: str
    companion_dialogue: str
    choices: list[EpisodeNodeChoice] = Field(default_factory=list)
    is_start_node: bool = False
    is_end_node: bool = False


class EpisodeCreate(BaseModel):
    """Request model to create an episode."""
    companion_id: str
    title: str
    description: str
    required_relationship_stage: int = 0  # 0=Stranger, 1=Curious, etc.
    script_nodes: list[EpisodeScriptNode]


class EpisodeResponse(BaseModel):
    """Response model for episode data."""
    id: str = Field(alias="_id")
    companion_id: str
    title: str
    description: str
    required_relationship_stage: int
    script_nodes: list[EpisodeScriptNode]
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class EpisodeInDB(BaseDBModel, TimestampMixin):
    """Episode document as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    companion_id: str
    title: str
    description: str
    required_relationship_stage: int
    script_nodes: list[EpisodeScriptNode]

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class EpisodeProgressInDB(BaseDBModel, TimestampMixin):
    """User's progress on an episode."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    episode_id: str
    companion_id: str
    status: str  # "not_started", "in_progress", "completed"
    current_node_id: Optional[str] = None
    total_xp_earned: int = 0
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class EpisodeProgressResponse(BaseModel):
    """Response model for episode progress."""
    id: str = Field(alias="_id")
    user_id: str
    episode_id: str
    companion_id: str
    status: str
    current_node_id: Optional[str] = None
    total_xp_earned: int
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class EpisodeChoiceRequest(BaseModel):
    """Request to make a choice in an episode."""
    episode_id: str
    choice_id: str


class EpisodeChoiceResponse(BaseModel):
    """Response after making a choice."""
    success: bool
    next_node: Optional[EpisodeScriptNode] = None
    xp_earned: int = 0
    total_xp_earned: int = 0
    is_completed: bool = False


# ============================================================================
# Companion Journal Models
# ============================================================================

class JournalEntryResponse(BaseModel):
    """Journal entry response model."""
    id: str = Field(alias="_id")
    user_id: str
    companion_id: str
    stage: int
    entry_text: str
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    is_read: bool
    generated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class JournalEntryInDB(BaseDBModel):
    """Journal entry document as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    stage: int  # 0-4 (Stranger to Confidant)
    entry_text: str
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    is_read: bool = False
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class JournalReadRequest(BaseModel):
    """Request to mark a journal entry as read."""
    pass


# ============================================================================
# Proactive Messaging Models
# ============================================================================

class ProactiveTriggerType(str, Enum):
    """Types of proactive message triggers."""
    GOOD_MORNING = "good_morning"
    MISS_YOU = "miss_you"
    MILESTONE_CONGRATS = "milestone_congrats"
    QUEST_REMINDER = "quest_reminder"
    STORY_NUDGE = "story_nudge"


class ProactiveTriggerInDB(BaseDBModel):
    """Proactive trigger document stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    trigger_type: ProactiveTriggerType
    scheduled_at: datetime
    processed_at: Optional[datetime] = None
    is_processed: bool = False
    context: dict = Field(default_factory=dict)  # Additional context for message generation
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class CompanionInitiatedMessageInDB(BaseDBModel):
    """Companion-initiated message stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    trigger_type: ProactiveTriggerType
    content: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    conversation_session_id: Optional[str] = None  # Reference to conversation session
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class ProactiveMessageResponse(BaseModel):
    """Response model for proactive messages."""
    id: str = Field(alias="_id")
    companion_id: str
    trigger_type: ProactiveTriggerType
    content: str
    sent_at: datetime
    is_read: bool

    model_config = ConfigDict(populate_by_name=True)


class UnreadProactiveMessagesResponse(BaseModel):
    """Response model for unread proactive messages grouped by companion."""
    companion_id: str
    companion_name: str
    unread_count: int
    messages: list[ProactiveMessageResponse]


class ProactiveHistoryResponse(BaseModel):
    """Response model for proactive message history with a companion."""
    messages: list[ProactiveMessageResponse]
    total: int
    page: int
    per_page: int


# ============================================================================
# Campus Quests Models
# ============================================================================

class QuestType(str, Enum):
    """Types of quests."""
    STUDY = "study"
    SOCIAL = "social"
    WELLNESS = "wellness"
    RIVALRY = "rivalry"


class QuestStatus(str, Enum):
    """Status of a user's quest."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestBase(BaseDBModel):
    """Base quest template as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    quest_id: str = Field(..., unique=True)
    title: str
    description: str
    companion_giver: str
    quest_type: QuestType
    xp_reward: int
    verification_method: str = "openrouter"  # "openrouter", "manual", or "auto"
    target_count: Optional[int] = None  # For auto quests requiring multiple actions (e.g., send 5 messages)
    trigger_event: Optional[str] = None  # For auto quests (e.g., "send_message", "start_study_session")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class UserQuestInDB(BaseDBModel):
    """User's active/completed quest as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    quest_id: str
    title: str
    description: str
    companion_giver: str
    quest_type: QuestType
    xp_reward: int
    verification_method: str = "openrouter"  # "openrouter", "manual", or "auto"
    target_count: Optional[int] = None
    trigger_event: Optional[str] = None
    progress_count: int = 0
    status: QuestStatus = QuestStatus.ACTIVE
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    user_report_text: Optional[str] = None
    verification_result: Optional[bool] = None
    retry_count: int = 0

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class UserQuestResponse(BaseModel):
    """Response model for user quest data."""
    id: str = Field(alias="_id")
    quest_id: str
    title: str
    description: str
    companion_giver: str
    quest_type: QuestType
    xp_reward: int
    verification_method: str = "openrouter"
    target_count: Optional[int] = None
    trigger_event: Optional[str] = None
    progress_count: int = 0
    status: QuestStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    user_report_text: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class QuestCompletionRequest(BaseModel):
    """Request to complete a quest."""
    report_text: str = Field(..., min_length=10, max_length=2000)


class QuestCompletionResponse(BaseModel):
    """Response after quest completion attempt."""
    success: bool
    verified: bool
    xp_earned: int
    message: str
    can_retry: bool = False


class QuestHistoryResponse(BaseModel):
    """Response model for quest history."""
    active: list[UserQuestResponse]
    completed: list[UserQuestResponse]
    failed: list[UserQuestResponse]


# ============================================================================
# Campus Lounge / Group Chat Models
# ============================================================================

class GroupMessageSenderType(str, Enum):
    """Type of message sender in group chat."""
    USER = "user"
    COMPANION = "companion"


class GroupMessageInDB(BaseDBModel):
    """Group chat message stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sender_type: GroupMessageSenderType
    sender_id: str  # user_id or companion_id (e.g., "oliver", "chloe")
    sender_name: str  # Display name
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None  # ID of message this is replying to

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class GroupMessageResponse(BaseModel):
    """Response model for group chat message."""
    id: str = Field(alias="_id")
    sender_type: GroupMessageSenderType
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime
    reply_to: Optional[str] = None
    sender_color: Optional[str] = None
    sender_avatar: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class GroupChatHistoryResponse(BaseModel):
    """Response model for group chat history."""
    messages: list[GroupMessageResponse]
    participants: list[dict]  # List of {id, name, color, avatar}
    total: int


class GroupChatSendRequest(BaseModel):
    """Request to send a message to group chat."""
    content: str = Field(..., min_length=1, max_length=1000)
    reply_to: Optional[str] = None


class GroupChatSendResponse(BaseModel):
    """Response after sending a group chat message."""
    user_message: GroupMessageResponse
    companion_replies: list[GroupMessageResponse]


class CompanionPersonalityConfig(BaseModel):
    """Configuration for companion personality in group chat."""
    companion_id: str
    name: str
    personality: str
    speech_patterns: str
    opinions: dict[str, str]  # Map of other companion IDs to opinions


# ============================================================================
# Study War Room / Study Mode Models
# ============================================================================

class StudySessionStatus(str, Enum):
    """Status of a study session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class StudySessionCreate(BaseModel):
    """Request to create a study session."""
    duration_minutes: int = Field(default=25, ge=5, le=120)
    companion_id: str = Field(default="study_buddy")
    focus_topic: Optional[str] = Field(default=None, max_length=200)


class StudySessionInDB(BaseDBModel):
    """Study session as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    companion_id: str
    duration_minutes: int
    focus_topic: Optional[str] = None
    status: StudySessionStatus = StudySessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expected_end_at: datetime
    completed_at: Optional[datetime] = None
    interruptions: int = 0
    xp_earned: int = 0
    companion_messages: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class StudySessionResponse(BaseModel):
    """Response model for study session."""
    id: str = Field(alias="_id")
    companion_id: str
    duration_minutes: int
    focus_topic: Optional[str] = None
    status: StudySessionStatus
    started_at: datetime
    expected_end_at: datetime
    completed_at: Optional[datetime] = None
    interruptions: int
    xp_earned: int
    time_remaining_seconds: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class StudyFocusCheckRequest(BaseModel):
    """Request to check focus status during study session."""
    session_id: str


class StudyFocusCheckResponse(BaseModel):
    """Response with focus status."""
    session_id: str
    status: StudySessionStatus
    time_remaining_seconds: int
    interruptions: int
    companion_message: Optional[str] = None


class StudyCompleteRequest(BaseModel):
    """Request to complete a study session."""
    session_id: str


class StudyCompleteResponse(BaseModel):
    """Response after completing study session."""
    session_id: str
    status: StudySessionStatus
    xp_earned: int
    completed_at: datetime
    companion_congratulations: str


class StudyLeaderboardEntry(BaseModel):
    """Entry in study leaderboard."""
    rank: int
    user_name: str
    total_focus_minutes: int
    completed_sessions: int


class StudyLeaderboardResponse(BaseModel):
    """Response with study leaderboard."""
    entries: list[StudyLeaderboardEntry]
    user_rank: Optional[int] = None
    user_total_minutes: Optional[int] = None
