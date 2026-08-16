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
    family: str  # Token family for rotation/revocation
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
    COMPANION_CHAT = "companion_chat"
    LOUNGE_ACTIVITY = "lounge_activity"
    STUDY_ROOM = "study_room"


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
    retry_count: int = 0
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
    retry_count: int = 0
    status: QuestStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    user_report_text: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


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


# ============================================================================
# Study Buddy Models
# ============================================================================

class StudyBuddyProfileCreate(BaseModel):
    """Request to create/update study buddy profile."""
    country: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    campus_university: str = Field(..., min_length=2, max_length=200)
    major: str = Field(..., min_length=2, max_length=100)
    academic_year: str = Field(..., min_length=1, max_length=50)
    strong_subjects: list[str] = Field(default_factory=list)
    weak_subjects: list[str] = Field(default_factory=list)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_id: Optional[str] = Field(None, max_length=100)


class StudyBuddyProfileUpdate(BaseModel):
    """Request to update study buddy profile."""
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    campus_university: Optional[str] = Field(None, min_length=2, max_length=200)
    major: Optional[str] = Field(None, min_length=2, max_length=100)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=50)
    strong_subjects: Optional[list[str]] = Field(default_factory=list)
    weak_subjects: Optional[list[str]] = Field(default_factory=list)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_id: Optional[str] = Field(None, max_length=100)

    @field_validator("country", "city", mode="after")
    @classmethod
    def validate_min_length_if_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that if a value is provided and not empty, it meets min length."""
        if v is not None and v != "" and len(v) < 2:
            raise ValueError("Must be at least 2 characters if provided")
        return v


class StudyBuddyProfileInDB(BaseDBModel, TimestampMixin):
    """Study buddy profile as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    country: str
    city: str
    campus_university: str
    major: str
    academic_year: str
    strong_subjects: list[str] = Field(default_factory=list)
    weak_subjects: list[str] = Field(default_factory=list)
    bio: Optional[str] = None
    avatar_id: Optional[str] = None
    is_online: bool = False
    last_active: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class StudyBuddyProfileResponse(BaseModel):
    """Response model for study buddy profile."""
    id: str = Field(alias="_id")
    user_id: str
    country: str
    city: str
    campus_university: str
    major: str
    academic_year: str
    strong_subjects: list[str]
    weak_subjects: list[str]
    bio: Optional[str]
    avatar_id: Optional[str]
    is_online: bool
    last_active: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class MatchReason(str, Enum):
    """Reasons for matching users."""
    STRONG_WEAK = "strong_weak"
    SAME_CAMPUS = "same_campus"
    SAME_MAJOR = "same_major"
    SAME_YEAR = "same_year"
    SAME_LOCATION = "same_location"
    RELATED_SUBJECTS = "related_subjects"


class MatchReasonResponse(BaseModel):
    """Match reason response."""
    reason: MatchReason
    description: str


class StudyBuddyMatchRequest(BaseModel):
    """Request for matching study buddies."""
    user_id: Optional[str] = None


class StudyBuddyMatchResult(BaseModel):
    """Match result for a study buddy."""
    user_id: str
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    compatibility_score: int  # 0-100
    match_reasons: list[MatchReasonResponse]
    strong_subjects_overlap: list[str]
    weak_subjects_help: list[str]
    # Public profile information
    country: str
    city: str
    campus_university: str
    major: str
    academic_year: str
    strong_subjects: list[str]
    weak_subjects: list[str]


class StudyBuddyMatchResponse(BaseModel):
    """Complete match response."""
    matches: list[StudyBuddyMatchResult]
    total_matches: int


class ConnectionRequestStatus(str, Enum):
    """Status of a connection request."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ConnectionRequestInDB(BaseDBModel, TimestampMixin):
    """Connection request as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sender_id: str
    recipient_id: str
    status: ConnectionRequestStatus = ConnectionRequestStatus.PENDING
    message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class ConnectionRequestCreate(BaseModel):
    """Request to create connection request."""
    recipient_id: str
    message: Optional[str] = Field(None, max_length=500)


class ConnectionRequestResponse(BaseModel):
    """Response model for connection request."""
    id: str = Field(alias="_id")
    sender_id: str
    recipient_id: str
    status: ConnectionRequestStatus
    message: Optional[str]
    sender_full_name: str
    sender_avatar_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class ConnectionResponse(BaseModel):
    """Response for user's connections."""
    id: str = Field(alias="_id")
    user_id: str
    full_name: str
    avatar_url: Optional[str] = None
    country: str
    city: str
    campus_university: str
    major: str
    academic_year: str
    is_online: bool

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Peer Q&A Models
# ============================================================================

class QuestionInDB(BaseDBModel, TimestampMixin):
    """Question as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    author_id: str
    content: str
    subject: str  # e.g., "Programming", "Mathematics", "Physics"
    images: list[str] = Field(default_factory=list)  # Array of image URLs
    answers_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class QuestionCreate(BaseModel):
    """Request to create a question."""
    content: str
    subject: str = Field(..., max_length=100)
    images: list[str] = Field(default_factory=list)


class QuestionResponse(BaseModel):
    """Response model for a question."""
    id: str = Field(alias="_id")
    author_id: str
    author_full_name: str
    content: str
    subject: str
    images: list[str]
    answers_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class QuestionUpdate(BaseModel):
    """Request to update a question."""
    content: Optional[str] = None
    subject: Optional[str] = None
    images: Optional[list[str]] = None


class AnswerInDB(BaseDBModel, TimestampMixin):
    """Answer as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    question_id: str
    author_id: str
    content: str
    images: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class AnswerCreate(BaseModel):
    """Request to create an answer."""
    question_id: str
    content: str
    images: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    """Response model for an answer."""
    id: str = Field(alias="_id")
    question_id: str
    author_id: str
    author_full_name: str
    content: str
    images: list[str]
    links: list[str]
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class AnswerUpdate(BaseModel):
    """Request to update an answer."""
    content: Optional[str] = None
    images: Optional[list[str]] = None
    links: Optional[list[str]] = None


class CommentInDB(BaseDBModel, TimestampMixin):
    """Comment as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    question_id: str
    author_id: str
    content: str
    parent_id: Optional[str] = None  # For threaded replies
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class CommentCreate(BaseModel):
    """Request to create a comment."""
    question_id: str
    content: str
    parent_id: Optional[str] = None


class CommentResponse(BaseModel):
    """Response model for a comment."""
    id: str = Field(alias="_id")
    question_id: str
    author_id: str
    author_full_name: str
    content: str
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class CommentUpdate(BaseModel):
    """Request to update a comment."""
    content: str


# ============================================================================
# Study Room Models
# ============================================================================

class StudyRoomStatus(str, Enum):
    """Status of a study room."""
    ACTIVE = "active"
    ENDED = "ended"


class StudyRoomInDB(BaseDBModel, TimestampMixin):
    """Study Room as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    host_id: str
    major: str
    subject: str
    title: str
    description: Optional[str] = None
    status: StudyRoomStatus = StudyRoomStatus.ACTIVE
    participant_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class StudyRoomCreate(BaseModel):
    """Request to create a study room."""
    major: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class StudyRoomResponse(BaseModel):
    """Response model for a study room."""
    id: str = Field(alias="_id")
    host_id: str
    host_full_name: str
    major: str
    subject: str
    title: str
    description: Optional[str]
    status: StudyRoomStatus
    participant_ids: list[str]
    participant_count: int
    max_participants: int = 5
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    model_config = ConfigDict(populate_by_name=True)


class StudyRoomUpdate(BaseModel):
    """Request to update a study room."""
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None


class StudyRoomJoinRequest(BaseModel):
    """Request to join a study room."""
    room_id: str


class StudyRoomParticipant(BaseModel):
    """Response for a study room participant."""
    id: str = Field(alias="_id")
    user_id: str
    full_name: str
    joined_at: datetime

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Study Buddy Messaging Models
# ============================================================================

class MessageType(str, Enum):
    """Types of messages."""
    TEXT = "text"


class ConversationInDB(BaseDBModel, TimestampMixin):
    """Conversation as stored in database (one-to-one between two users)."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_a_id: str
    user_b_id: str

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class ConversationCreate(BaseModel):
    """Request to create conversation (if doesn't exist)."""
    user_id: Optional[str] = None  # Ignored; user_id always comes from the authenticated JWT token
    other_user_id: str  # The other user in the conversation


class ConversationResponse(BaseModel):
    """Response model for conversation."""
    id: str = Field(alias="_id")
    user_a_id: str
    user_b_id: str
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)


class MessageInDB(BaseDBModel, TimestampMixin):
    """Message as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: str
    sender_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    is_read: bool = False
    read_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class MessageCreate(BaseModel):
    """Request to create message."""
    conversation_id: str
    content: str


class MessageResponse(BaseModel):
    """Response model for message."""
    id: str = Field(alias="_id")
    conversation_id: str
    sender_id: str
    content: str
    message_type: MessageType
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )


class MessageListResponse(BaseModel):
    """Paginated response for messages."""
    messages: list[MessageResponse]
    meta: PaginationMeta


class ConversationMessageResponse(BaseModel):
    """Response with conversation and messages."""
    conversation: ConversationResponse
    messages: list[MessageResponse]
    meta: PaginationMeta


# ============================================================================
# Study Room Messaging Models
# ============================================================================

class RoomMessageInDB(BaseDBModel, TimestampMixin):
    """Room message as stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    room_id: str
    sender_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    is_read: bool = False
    read_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )


class RoomMessageCreate(BaseModel):
    """Request to create room message."""
    content: str


class RoomMessageResponse(BaseModel):
    """Response model for room message."""
    id: str = Field(alias="_id")
    room_id: str
    sender_id: str
    content: str
    message_type: MessageType
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)
