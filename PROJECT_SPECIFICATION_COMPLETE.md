# AI Campus Companion - Complete Project Specification

## 1. PROJECT OVERVIEW

### Purpose
**AI Campus Companion** is a full-stack web application that provides personalized, AI-powered virtual companions for college students. The app features multiple AI companions with distinct personalities that users can interact with through text-based chat, story-driven scenarios, and gamified features.

### Problem Solved
- **Loneliness & Isolation**: College students often feel isolated; companions provide daily support and interaction
- **Lack of Academic Support**: Students need study partners but may not have access to consistent academic help
- **Need for Social Connection**: Campus social interactions can be intimidating; the lounge provides a low-pressure social space
- **Personalization**: Generic AI responses don't match individual user needs; companions adapt through RL training

### End Users
- **Primary**: College/university students aged 18-25
- **Secondary**: Educators who want to use companions as learning aids

### App Type
**Full-stack web application** with separate backend (FastAPI) and frontend (React) components, accessible via web browser.

---

## 2. TECH STACK

### Backend Technologies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Runtime** | Python | 3.x (unspecified) | Application runtime |
| **Web Framework** | FastAPI | 0.115.6 | REST API framework |
| **ASGI Server** | Uvicorn | 0.30.6 | ASGI server for FastAPI |
| **Database** | MongoDB | - | NoSQL document database via Motor |
| **ORM/ODM** | PyMongo Motor | 4.8.0+ | Async MongoDB driver |
| **Auth** | JWT (PyJWT) | 2.8.0 | Token-based authentication |
| **Password Hashing** | bcrypt | 4.1.2 | Secure password storage (12 rounds) |
| **HTTP Client** | httpx | 0.27.2 | Async HTTP client for OpenRouter |
| **ML Framework** | PyTorch | >=2.1.0 | Deep learning for RL training |
| **ML Tools** | Transformers | >=4.35.0 | Hugging Face transformers |
| **ML Tools** | Datasets | >=2.14.0 | Hugging Face datasets |
| **ML Tools** | scikit-learn | >=1.3.0 | Machine learning utilities |
| **ML Tools** | FAISS-CPU | 1.13.2 | Vector similarity search |
| **Vector DB** | FAISS | - | Embedding storage and retrieval |
| **ML Tools** | NumPy | <2.0 | Numerical computing |
| **ML Tools** | Pandas | 2.2.3 | Data manipulation |
| **ML Tools** | APScheduler | >=3.10.0 | Background job scheduling |
| **Email** | aiosmtplib | 3.0.2 | Async SMTP client |
| **Validation** | Pydantic | - | Data validation (v2) |
| **Config** | Pydantic Settings | 2.6.1 | Configuration management |
| **Security** | python-jose[cryptography] | 3.3.0 | JWT library |
| **Utilities** | python-dateutil | 2.9.0 | Date/time parsing |
| **Testing** | pytest | 8.3.3 | Test framework |
| **Testing** | pytest-asyncio | 0.24.0 | Async testing support |
| **Code Quality** | black | 24.10.0 | Code formatter |
| **Code Quality** | flake8 | 7.1.1 | Linter |
| **Code Quality** | mypy | 1.13.0 | Type checker |
| **Code Quality** | isort | 5.13.2 | Import sorter |

### Frontend Technologies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | React | 18.3.1 | UI library |
| **Build Tool** | Vite | 6.3.5 | Build tool and dev server |
| **Language** | TypeScript | - | Type-safe development |
| **State Management** | Zustand | ^5.0.11 | Lightweight state store |
| **UI Components** | Material-UI (MUI) | 7.3.5 | React component library |
| **UI Components** | Radix UI | Various versions | Accessible primitive components |
| **Styling** | Tailwind CSS | 4.1.12 | Utility-first CSS framework |
| **Styling** | @emotion/react | 11.14.0 | CSS-in-JS library |
| **Routing** | React Router | 7.13.0 | Client-side routing |
| **HTTP Client** | Axios | ^1.18.1 | HTTP client |
| **Animations** | Motion (Framer Motion) | 12.23.24 | Animation library |
| **Charts** | Recharts | 2.15.2 | Charting library |
| **Icons** | Lucide React | 0.487.0 | Icon library |
| **Date Handling** | date-fns | 3.6.0 | Date utilities |
| **Validation** | react-hook-form | 7.55.0 | Form validation |
| **Interaction** | react-dnd | 16.0.1 | Drag and drop |
| **Slider** | embla-carousel-react | 8.6.0 | Carousel component |
| **Input** | react-otp-input | 1.4.2 | OTP input field |
| **Notifications** | sonner | 2.0.3 | Toast notifications |
| **Icons** | canvas-confetti | ^1.9.4 | Celebration effects |

### External Services

| Service | Purpose | API Key Required |
|---------|---------|------------------|
| **OpenRouter** | AI model API for companion responses | ✅ Required |
| **MongoDB** | Database storage | ⚠️ Optional (runs without in dev) |
| **SMTP (Gmail)** | Email verification and password reset | ⚠️ Optional |

---

## 3. PROJECT STRUCTURE & ARCHITECTURE

### Directory Tree

```
FYP-AI_Campus_Companion/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── api/                      # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth_routes.py        # Authentication (register, login, OTP)
│   │   │   ├── chat_routes.py        # Chat endpoints with dual pipeline
│   │   │   ├── health_routes.py      # Health check endpoints
│   │   │   ├── journals.py           # Companion journal endpoints
│   │   │   ├── memory_routes.py      # Memory/scenario endpoints
│   │   │   ├── media.py              # Media handling (placeholder)
│   │   │   ├── episodes.py           # Story episodes/quests endpoints
│   │   │   ├── proactive.py          # Proactive messaging triggers
│   │   │   ├── quests.py             # Campus quest system endpoints
│   │   │   ├── group_chat.py         # Campus lounge endpoints
│   │   │   └── study.py              # Study room endpoints
│   │   ├── companions/                # Companion definitions
│   │   │   ├── __init__.py
│   │   │   ├── companions.py          # Companion templates and routing
│   │   │   └── prompt_builder.py      # LLM prompt construction
│   │   ├── core/                     # Core modules
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # JWT auth, password hashing
│   │   │   ├── database.py           # MongoDB connection management
│   │   │   ├── decorators.py         # Custom decorators
│   │   │   ├── error_responses.py    # Standardized error handling
│   │   │   ├── logging.py            # Logging configuration
│   │   │   ├── middleware.py         # Security middleware
│   │   │   ├── security.py           # Input sanitization, email masking
│   │   │   └── validation.py         # Request validation
│   │   ├── exceptions.py             # Custom exceptions
│   │   ├── memory/                   # Memory management
│   │   │   ├── __init__.py
│   │   │   ├── companion_memory.py   # Individual companion memories
│   │   │   ├── companion_memory_store.py
│   │   │   ├── embedding_client.py   # OpenRouter embeddings
│   │   │   └── memory.py             # Legacy memory store
│   │   ├── ml/                       # Machine Learning
│   │   │   ├── __init__.py
│   │   │   ├── rl_agent.py           # RL agent implementation
│   │   │   ├── rl_training.py        # Offline RL training pipeline
│   │   │   ├── rl_worker.py          # Background RL training worker
│   │   │   └── xp_evaluator.py       # XP reward calculation
│   │   ├── models.py                 # Pydantic data models
│   │   ├── services/                 # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── email_service.py      # SMTP email handling
│   │   │   ├── episode_service.py    # Episode seeding
│   │   │   ├── group_chat_service.py # Campus lounge logic
│   │   │   ├── journal_service.py    # Journal generation
│   │   │   ├── openrouter_client.py  # OpenRouter API wrapper
│   │   │   ├── otp_service.py        # OTP generation and verification
│   │   │   ├── proactive_service.py  # Proactive message scheduling
│   │   │   ├── quest_service.py      # Quest generation and verification
│   │   │   └── study_service.py      # Study room functionality
│   │   ├── utils/                    # Utility modules
│   │   │   ├── __init__.py
│   │   │   ├── rate_limiter.py       # Rate limiting implementation
│   │   │   └── session_manager.py    # Conversation session management
│   │   ├── constants/                # Constants and error codes
│   │   │   └── error_codes.py        # Standardized error codes
│   │   ├── config.py                 # Configuration management
│   │   ├── exceptions.py
│   │   └── main.py                   # FastAPI app factory
│   ├── tests/                        # Test suite
│   │   ├── __init__.py
│   │   └── ...
│   ├── uploads/                      # File uploads directory
│   ├── .pytest_cache/                # Pytest cache
│   ├── .env.example                  # Environment variable template
│   ├── requirements.txt              # Python dependencies
│   ├── main.py                       # Application entry point
│   └── venv/                         # Python virtual environment
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── app/                      # Main app structure
│   │   │   ├── App.tsx               # Root component
│   │   │   ├── store.ts              # Zustand state management
│   │   │   ├── routes.tsx            # React Router configuration
│   │   │   ├── styles/               # Global styles
│   │   │   │   └── index.css
│   │   │   ├── pages/                # Page components (25 files)
│   │   │   │   ├── Landing.tsx       # Landing page
│   │   │   │   ├── Login.tsx
│   │   │   │   ├── Signup.tsx
│   │   │   │   ├── VerifyEmail.tsx
│   │   │   │   ├── ForgotPassword.tsx
│   │   │   │   ├── CompanionSelection.tsx
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Chat.tsx
│   │   │   │   ├── UserProfile.tsx
│   │   │   │   ├── SettingsPersonal.tsx
│   │   │   │   ├── SettingsSecurity.tsx
│   │   │   │   ├── SettingsNotifications.tsx
│   │   │   │   ├── SupportHelpCenter.tsx
│   │   │   │   ├── SupportContact.tsx
│   │   │   │   ├── SupportTerms.tsx
│   │   │   │   ├── Payment.tsx
│   │   │   │   ├── CompanionProfilePage.tsx
│   │   │   │   ├── EpisodesListPage.tsx
│   │   │   │   ├── EpisodePlayer.tsx
│   │   │   │   ├── JournalPage.tsx
│   │   │   │   ├── QuestsPage.tsx
│   │   │   │   ├── QuestBoardPage.tsx
│   │   │   │   ├── GroupChatPage.tsx
│   │   │   │   └── StudyRoomPage.tsx
│   │   │   ├── layouts/              # Layout components
│   │   │   │   ├── AuthLayout.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   ├── components/           # Reusable components
│   │   │   │   ├── ui/               # MUI + Radix UI primitives
│   │   │   │   │   ├── accordion.tsx
│   │   │   │   │   ├── alert.tsx
│   │   │   │   │   ├── avatar.tsx
│   │   │   │   │   ├── button.tsx
│   │   │   │   │   ├── card.tsx
│   │   │   │   │   ├── dialog.tsx
│   │   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   │   ├── input.tsx
│   │   │   │   │   ├── label.tsx
│   │   │   │   │   ├── select.tsx
│   │   │   │   │   ├── slider.tsx
│   │   │   │   │   ├── switch.tsx
│   │   │   │   │   ├── tabs.tsx
│   │   │   │   │   ├── tooltip.tsx
│   │   │   │   │   └── ...
│   │   │   │   ├── EpisodeCard.tsx
│   │   │   │   ├── EpisodePlayer.tsx
│   │   │   │   ├── GroupChatMessage.tsx
│   │   │   │   ├── JournalTimeline.tsx
│   │   │   │   ├── NotificationBell.tsx
│   │   │   │   ├── QuestCard.tsx
│   │   │   │   ├── StudyTimer.tsx
│   │   │   │   ├── ProactiveToast.tsx
│   │   │   │   └── figma/            # Figma plugin components
│   │   │   ├── hooks/                # Custom React hooks
│   │   │   ├── stores/               # Additional Zustand stores
│   │   │   │   └── useQuestStore.ts  # Quest-specific state
│   │   │   └── utils/                # Frontend utilities
│   │   ├── assets/                   # Static assets
│   │   └── main.tsx                  # App entry point
│   ├── public/                       # Public assets
│   ├── dist/                         # Built output
│   ├── node_modules/
│   ├── package.json                  # NPM dependencies
│   └── vite.config.ts                # Vite configuration
│
├── .claude/                          # Claude Code configuration
├── .git/                             # Git repository
├── .gitignore
├── ATTRIBUTIONS.md                   # Third-party attributions
├── commands.txt                      # Development commands
├── clear_rate_limits.py              # Rate limit cleanup script
├── IMPLEMENTATION_SUMMARY.md         # Implementation notes
├── MANGA_INTEGRATION_TESTING.md      # Manga feature testing guide
├── PROJECT_SPECIFICATION_COMPLETE.md # This file
└── [Other documentation files...]
```

### Architecture Pattern

**Monolithic Full-Stack Architecture** with separation of concerns:
- **Backend**: FastAPI REST API with modular route handlers
- **Frontend**: React SPA with client-side routing
- **Communication**: RESTful API over HTTP with JWT authentication
- **State Management**: Zustand (frontend) + Backend state (MongoDB)
- **Database**: MongoDB (NoSQL, document-oriented)

### Entry Points

**Backend**:
- `backend/main.py` - Application factory and FastAPI app instance
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` - Run server

**Frontend**:
- `frontend/src/main.tsx` - React entry point
- `npm run dev` - Start dev server (port 5173)
- `npm run build` - Production build

---

## 4. DATABASE SCHEMA

### MongoDB Collections

#### 1. **users** (Main user collection)
```javascript
{
  "_id": ObjectId,
  "email": String (unique),
  "full_name": String,
  "password_hash": String (bcrypt hashed),
  "role": Enum [USER, ADMIN, MODERATOR],
  "is_verified": Boolean,
  "is_active": Boolean,
  "failed_login_attempts": Integer,
  "locked_until": Date | null,
  "last_login": Date | null,
  "email_verified_at": Date | null,
  "companion_progression": Array[CompanionProgression],
  "created_at": Date,
  "updated_at": Date
}
```
**Indexes**:
- `email` (unique)
- `created_at`
- `[is_verified, is_active]`

**Relationships**: Referenced by most other collections via `user_id`

---

#### 2. **otps** (One-time passwords)
```javascript
{
  "_id": ObjectId,
  "email": String,
  "otp": String (hashed via pepper + bcrypt),
  "purpose": Enum [REGISTRATION, PASSWORD_RESET, EMAIL_CHANGE],
  "expires_at": Date,
  "attempts": Integer,
  "created_at": Date
}
```
**Indexes**:
- `expires_at` (TTL - 10 minutes)
- `[email, purpose]` (compound)

---

#### 3. **token_blacklist** (JWT token revocation)
```javascript
{
  "_id": ObjectId,
  "token_jti": String (unique),
  "expires_at": Date,
  "created_at": Date
}
```
**Indexes**:
- `expires_at` (TTL)
- `token_jti` (unique)

---

#### 4. **revoked_tokens** (Refresh token rotation)
```javascript
{
  "_id": ObjectId,
  "token_jti": String,
  "user_id": String,
  "family": String (token family for revocation),
  "expires_at": Date,
  "revoked_at": Date
}
```
**Indexes**:
- `expires_at` (TTL)
- `family`
- `[user_id, family]`

---

#### 5. **rate_limits** (Rate limiting)
```javascript
{
  "_id": ObjectId,
  "key": String (identifier: email:..., ip:...),
  "count": Integer,
  "window_start": Date,
  "expires_at": Date,
  "reset_timestamp": Date
}
```
**Indexes**:
- `expires_at` (TTL)
- `key` (unique)

---

#### 6. **conversation_sessions** (Chat history per companion)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "messages": Array[{
    "role": "user" | "assistant" | "system",
    "content": String,
    "timestamp": Date
  }],
  "xp_earned": Integer,
  "relationship_delta": Integer,
  "rl_actions_taken": Array[{
    "action_type": String,
    "intensity": Float
  }],
  "episode_id": String | null,
  "started_at": Date,
  "ended_at": Date | null,
  "is_active": Boolean
}
```
**Indexes**:
- `[user_id, companion_id, started_at]`
- `[user_id, companion_id, is_active]`

---

#### 7. **rl_transitions** (Reinforcement learning training data)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "state": Object (serialized ConversationState),
  "action": Object {
    "action_type": String,
    "intensity": Float,
    "topic_focus": String
  },
  "reward": Float,
  "next_state": Object,
  "done": Boolean,
  "created_at": Date
}
```
**Indexes**:
- `[companion_id, created_at]`
- `[user_id, companion_id]`

---

#### 8. **companion_memories** (Individual companion memories with embeddings)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "memory_type": String ("conversation", "story", "feedback", "fact"),
  "content": String,
  "metadata": Object,
  "importance": Float,
  "embedding": Array[Float],
  "created_at": Date
}
```
**Indexes**:
- `[user_id, companion_id, created_at]`
- `[user_id, companion_id, memory_type]`

---

#### 9. **episodes** (Story episodes for companions)
```javascript
{
  "_id": ObjectId,
  "companion_id": String,
  "title": String,
  "description": String,
  "required_relationship_stage": Integer,
  "script_nodes": Array[{
    "node_id": String,
    "companion_dialogue": String,
    "choices": Array[{
      "choice_id": String,
      "choice_text": String,
      "next_node_id": String | null,
      "xp_reward": Integer
    }],
    "is_start_node": Boolean,
    "is_end_node": Boolean
  }],
  "created_at": Date
}
```
**Indexes**:
- `[companion_id, required_relationship_stage]`

---

#### 10. **episode_progress** (User episode progress)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "episode_id": String,
  "companion_id": String,
  "status": Enum [not_started, in_progress, completed],
  "current_node_id": String | null,
  "total_xp_earned": Integer,
  "completed_at": Date | null
}
```
**Indexes**:
- `[user_id, companion_id]` (unique per user-companion)
- `[user_id, episode_id]` (unique per user-episode)

---

#### 11. **companion_journals** (Private diary entries per relationship stage)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "stage": Integer (0-4),
  "entry_text": String,
  "is_unlocked": Boolean,
  "unlocked_at": Date | null,
  "is_read": Boolean,
  "generated_at": Date,
  "read_at": Date | null
}
```
**Indexes**:
- `[user_id, companion_id, stage]` (unique)
- `[user_id, companion_id]`

---

#### 12. **proactive_triggers** (Scheduled proactive messages)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "trigger_type": Enum [GOOD_MORNING, MISS_YOU, MILESTONE_CONGRATS, QUEST_REMINDER, STORY_NUDGE],
  "scheduled_at": Date,
  "processed_at": Date | null,
  "is_processed": Boolean,
  "context": Object,
  "created_at": Date
}
```
**Indexes**:
- `[user_id, companion_id, trigger_type]`
- `[is_processed, scheduled_at]`
- `created_at` (TTL - 30 days)

---

#### 13. **companion_initiated_messages** (Saved proactive messages)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "trigger_type": Enum [GOOD_MORNING, MISS_YOU, MILESTONE_CONGRATS, QUEST_REMINDER, STORY_NUDGE],
  "content": String,
  "is_read": Boolean,
  "read_at": Date | null,
  "conversation_session_id": String | null,
  "created_at": Date
}
```
**Indexes**:
- `[user_id, companion_id, is_read]`
- `[user_id, created_at]`
- `created_at` (TTL - 90 days)

---

#### 14. **proactive_email_logs** (Email sending audit trail)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "trigger_type": String,
  "recipient_email": String,
  "companion_id": String,
  "status": String,
  "sent_at": Date,
  "created_at": Date
}
```
**Indexes**:
- `[user_id, sent_at]`
- `sent_at` (TTL - 30 days)

---

#### 15. **user_quests** (Daily campus quests)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "quest_id": String (unique per user),
  "title": String,
  "description": String,
  "companion_giver": String,
  "quest_type": Enum [COMPANION_CHAT, LOUNGE_ACTIVITY, STUDY_ROOM],
  "xp_reward": Integer,
  "verification_method": String,
  "target_count": Integer | null,
  "trigger_event": String | null,
  "progress_count": Integer,
  "retry_count": Integer,
  "status": Enum [active, completed, failed],
  "started_at": Date,
  "completed_at": Date | null,
  "user_report_text": String | null,
  "verification_result": Boolean | null,
  "created_at": Date
}
```
**Indexes**:
- `[status, created_at]`
- `[user_id, quest_id]`

---

#### 16. **study_sessions** (Study room sessions)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "companion_id": String,
  "duration_minutes": Integer,
  "focus_topic": String | null,
  "status": Enum [active, completed, interrupted],
  "started_at": Date,
  "expected_end_at": Date,
  "completed_at": Date | null,
  "interruptions": Integer,
  "xp_earned": Integer,
  "companion_messages": Array[Object]
}
```
**Indexes**: Not explicitly documented but would follow standard patterns

---

### ER Diagram (Text Format)

```
┌─────────────┐         ┌──────────────┐
│   users     │ ◄──────►│otp           │
│             │         │              │
│ •email      │         │•email        │
│ •full_name  │         │•purpose      │
│ •password   │         │•expires_at   │
│ •role       │         │              │
│ •is_verified├────────►│              │
└─────────────┘         └──────────────┘
      │
      ├──────────────────┬─────────────────┬─────────────┐
      │                  │                 │             │
      ▼                  ▼                 ▼             ▼
┌─────────────┐    ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│conversation │    │episode       │  │proactive     │  │user_quests  │
│sessions     │    │              │  │triggers      │  │             │
│             │    │•title        │  │•trigger_type │  │•quest_id    │
│•user_id     │    │•script_nodes │  │•scheduled_at │  │•status      │
│•companion_id├────┤•choices      │  │•is_processed │  └─────────────┘
└─────────────┘    └──────────────┘  └──────────────┘
      │
      ├─────────────┐    ┌──────────────┐
      ▼             │    │               │
┌─────────────┐    │    │               │
│rl_transitions├────┤               │
│             │    │    │               │
│•user_id     │    │    │               │
│•companion_id├────┘    │               │
└─────────────┘         │               │
      │                 │               │
      └─────────────────┼───────────────┘
                        ▼
              ┌──────────────────┐
              │companion_memories│
              │                  │
              │•user_id          │
              │•companion_id     │
              │•embedding        │
              └──────────────────┘

[Frontend ↔ Backend via JWT tokens]
```

### Relationships Summary

- **User** → **Companion**: One-to-many (user has 5 companion slots)
- **User** → **Conversation Session**: One-to-many
- **User** → **Episode Progress**: One-to-many
- **User** → **Quest**: One-to-many (active/completed)
- **Companion** → **Episodes**: One-to-many
- **Companion** → **Journal Entries**: One-to-many (by stage)

---

## 5. API ENDPOINTS & BACKEND LOGIC

### Base URL
`http://localhost:8000/api` (development) or production URL

### Authentication Routes (`/auth`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| POST | `/auth/register` | `email`, `full_name`, `password` | `success`, `message`, `user_id` | No | User registration with OTP |
| POST | `/auth/verify-otp` | `email`, `otp`, `purpose` | `success`, `message` | No | Email verification |
| POST | `/auth/resend-otp` | `email`, `purpose` | `success`, `message` | No | Resend verification code |
| POST | `/auth/login` | `email`, `password` | `access_token`, `refresh_token`, `user` | No | User login |
| POST | `/auth/refresh` | `refresh_token` (Bearer) | `access_token`, `refresh_token` | No | Refresh access token |
| POST | `/auth/logout` | `access_token` (Bearer) | `success`, `message` | Yes | Logout and blacklist token |
| GET | `/auth/me` | - | `user` profile | Yes | Get current user info |
| POST | `/auth/forgot-password` | `email` | `success`, `message` | No | Request password reset |
| POST | `/auth/reset-password` | `email`, `otp`, `new_password` | `success`, `message` | No | Reset password |

**Key Features**:
- Rate limiting on login (5 attempts per 15 min per email)
- Account lockout after 5 failed attempts (30 min lock)
- Timing-constant response to prevent user enumeration
- OTP hashing with pepper + bcrypt
- JWT token rotation with family tracking
- Token blacklist for logout
- Token refresh with automatic rotation

---

### Chat Routes (`/chat`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| GET | `/chat/companions` | - | `[{id, name, tier}]` | No | List all companions |
| POST | `/chat` | `companion_key`, `message`, `episode_id`, `scenario_text` | `companion`, `reply`, `xp_delta`, `level`, etc. | Yes | Send chat message (dual pipeline) |
| POST | `/chat/companion/{id}/unlock-level` | - | `success`, `level` | Yes | Unlock companion level |
| GET | `/chat/progression/{companion_id}` | - | `companion_id`, `xp`, `level`, `relationship_stage` | Yes | Get progression stats |
| GET | `/chat/progression` | - | `[CompanionProgression]` | Yes | Get all progressions |
| DELETE | `/chat/companion/{companion_id}` | - | `success`, `message` | Yes | Delete companion |

**Dual Pipeline Architecture**:

1. **Trainable Pipeline** (`philosopher`, `rival`):
   - Server-side XP evaluation
   - RL action selection
   - Memory retrieval (semantic search)
   - Session tracking
   - Journal generation triggers
   - RL transition storage
   - Companion-specific model routing

2. **Demo Pipeline** (`study_buddy`, `party_friend`, `freshman`):
   - Lightweight prompt-based chat
   - Client-side XP evaluation
   - Basic conversation history
   - Generic model (Llama 3.3 70B)

**XP Evaluation Rules**:
- Toxic words: -5 XP
- Breaks immersion: -2 XP
- Spam repetition: -1 XP
- Low effort (<2 chars): -1 XP
- Story interaction (active scenario + 8+ chars): +15 XP
- Thoughtful response (25+ chars): +12 XP
- Normal message (8-25 chars): +10 XP

**Relationship Stages**:
- Stranger: 0 points
- Curious: 50 points
- Friend: 150 points
- Close Friend: 300 points
- Confidant: 500 points

---

### Quest Routes (`/quests`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| POST | `/quests/generate` | - | `success`, `quests_count` | Yes | Manually generate quests (testing) |
| GET | `/quests/active` | `limit`, `offset` | `data`, `pagination` | Yes | Get active quests |
| POST | `/quests/complete/{quest_id}` | `report_text` | `success`, `verified`, `xp_earned` | Yes | Submit quest completion |
| GET | `/quests/history` | `limit`, `offset` | `data`, `pagination` | Yes | Get quest history |
| GET | `/quests/{quest_id}` | - | `quest` details | Yes | Get specific quest |

**Daily Quest Templates**:
1. **Chat Quest**: Send first message (25 XP)
2. **Chat Quest**: Send 10 messages (25 XP)
3. **Lounge Quest**: Join lounge chat (25 XP)
4. **Lounge Quest**: Send 5 messages in lounge (25 XP)
5. **Study Quest**: Study 30 minutes (50 XP)

**Quest Verification**:
- Uses OpenRouter to verify report text
- Allows one retry if verification fails
- Awards XP if verified
- Marks quest as completed/failed

---

### Journal Routes (`/journals`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| GET | `/journals/{companion_id}` | `limit`, `offset` | `data`, `pagination` | Yes | Get unlocked journals |
| GET | `/journals/{companion_id}/{stage}` | - | `journal` entry | Yes | Get specific journal |
| POST | `/journals/{companion_id}/{stage}/read` | - | `journal` (marked read) | Yes | Mark journal as read |

**Journal Stages** (0-4):
- Stage 0: Stranger
- Stage 1: Curious
- Stage 2: Friend
- Stage 3: Close Friend
- Stage 4: Confidant

**Auto-Generation**: Journals generate when relationship stage increases (via daily job at 2 AM)

---

### Group Chat Routes (`/group-chat`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| POST | `/group-chat/messages` | `content`, `reply_to` | `user_message`, `companion_replies` | Yes | Send lounge message |
| GET | `/group-chat/messages` | `limit`, `offset`, `before` | `data`, `participants`, `pagination` | Yes | Get lounge history |

**Companions in Lounge**:
- Oliver (study_buddy)
- Chloe (party_friend)
- Toby (freshman)

**Quest Integration**: Sending messages tracks for quest progression

---

### Study Routes (`/study`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| POST | `/study/sessions` | `duration_minutes`, `companion_id`, `focus_topic` | `session` | Yes | Create study session |
| GET | `/study/sessions/{session_id}` | - | `session` | Yes | Get session details |
| POST | `/study/sessions/{session_id}/complete` | - | `session` | Yes | Complete session |
| GET | `/study/leaderboard` | - | `entries`, `user_rank` | Yes | Get study leaderboard |

**XP Calculation**:
- Base: 10 XP
- Duration bonus: 1 XP per minute
- Interruption penalty: -5 XP per interruption
- Minimum: 5 XP

**Leaderboard**: Tracks total focus minutes across all users

---

### Memory Routes (`/memory`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| POST | `/memory/scenario/unlock` | `user_id`, `companion_id`, `title`, `scenario`, `backstory`, `narration` | - | Yes | Store active scenario |
| GET | `/memory/scenario/latest/{companion_id}` | - | `scenario` | Yes | Get latest scenario |
| GET | `/memory/scenario/conversation/{companion_id}` | - | `messages` | Yes | Get conversation history |

---

### Episodes Routes (`/episodes`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| GET | `/episodes` | - | `[Episodes]` | Yes | List all episodes |
| GET | `/episodes/{episode_id}` | - | `episode` | Yes | Get episode details |
| GET | `/episodes/{companion_id}/progress` | - | `progress` | Yes | Get episode progress |
| POST | `/episodes/{episode_id}/complete` | - | `success` | Yes | Mark episode complete |
| GET | `/episodes/{companion_id}/completed` | - | `[completed episodes]` | Yes | Get completed episodes |

---

### Proactive Routes (`/proactive`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| GET | `/proactive/messages` | - | `unread messages grouped by companion` | Yes | Get proactive messages |
| POST | `/proactive/{message_id}/read` | - | `success` | Yes | Mark message read |
| GET | `/proactive/{companion_id}/history` | `limit`, `offset` | `messages`, `pagination` | Yes | Get message history |

**Trigger Types**:
- `good_morning`: 7 AM daily
- `miss_you`: Based on inactivity
- `milestone_congrats`: Relationship stage milestones
- `quest_reminder`: 30 min after quest creation
- `story_nudge`: Encourage episode interaction

**Scheduling**: Triggers check every 6 hours

---

### Health Routes (`/health`)

| Method | Endpoint | Request Body | Response | Auth Required | Purpose |
|--------|----------|--------------|----------|---------------|---------|
| GET | `/health` | - | `status`, `database`, `timestamp` | No | Health check endpoint |

---

### Middleware Functions

1. **MaxBodySizeMiddleware** (1 MB limit)
2. **Security Middleware**:
   - Request ID tracking
   - CORS handling
   - Rate limiting
   - Authentication verification
3. **Error Handling**:
   - AppException handler
   - HTTPException handler
   - Global exception handler
4. **Logging Middleware**:
   - Request ID injection
   - Error redaction
   - Performance tracking

---

### Background Jobs (APScheduler)

| Job | Schedule | Description |
|-----|----------|-------------|
| `daily_journal_generation` | Daily at 2:00 AM | Generate missing journal entries for all users |
| `proactive_schedule_triggers` | Every 6 hours | Schedule proactive message triggers |
| `proactive_process_triggers` | Every 30 minutes | Process pending triggers |
| `daily_quest_generation` | Daily at 6:00 AM | Generate daily quests for all users |

---

## 6. FRONTEND STRUCTURE

### Pages (25 total)

| Page | Route | Layout | Features |
|------|-------|--------|----------|
| **Landing** | `/` | None | Hero section, companion showcase, features |
| **Login** | `/login` | AuthLayout | Email/password login with error handling |
| **Signup** | `/signup` | AuthLayout | Registration with OTP verification |
| **VerifyEmail** | `/verify-email` | AuthLayout | OTP input and verification |
| **ForgotPassword** | `/forgot-password` | AuthLayout | Password reset request |
| **CompanionSelection** | `/select` | None | Choose your first companion |
| **Payment** | `/upgrade` | None | Subscription page (placeholder) |
| **Dashboard** | `/app` | MainLayout | Overview, active quests, recent messages |
| **Chat** | `/app/chat/:id` | MainLayout | Chat interface with companion |
| **UserProfile** | `/app/me` | MainLayout | User settings and profile |
| **SettingsPersonal** | `/app/settings/personal` | MainLayout | Personal information |
| **SettingsSecurity** | `/app/settings/security` | MainLayout | Password and auth settings |
| **SettingsNotifications** | `/app/settings/notifications` | MainLayout | Notification preferences |
| **SupportHelpCenter** | `/app/support/help` | MainLayout | Help documentation |
| **SupportContact** | `/app/support/contact` | MainLayout | Contact form |
| **SupportTerms** | `/app/support/terms` | MainLayout | Terms of service |
| **CompanionProfilePage** | `/app/companion/:id/profile` | MainLayout | Companion profile details |
| **EpisodesListPage** | `/app/companion/:id/episodes` | MainLayout | List of story episodes |
| **EpisodePlayer** | `/app/companion/:id/episodes/play/:episodeId` | MainLayout | Interactive story player |
| **JournalPage** | `/app/companion/:id/journal` | MainLayout | Private journal entries |
| **QuestsPage** | `/app/quests` | MainLayout | Quest board with completion |
| **QuestBoardPage** | `/app/quests/*` | MainLayout | Quest tracking and history |
| **GroupChatPage** | `/app/campus-lounge` | MainLayout | Campus lounge chat |
| **StudyRoomPage** | `/app/study-room` | MainLayout | Study timer and focus mode |

---

### Components

#### Core Components
- **EpisodeCard** - Display episode with progress
- **EpisodePlayer** - Interactive story with branching choices
- **GroupChatMessage** - Message bubble with sender info
- **JournalTimeline** - Timeline view of journal entries
- **NotificationBell** - Proactive message alerts
- **QuestCard** - Quest display with progress
- **StudyTimer** - Pomodoro-style timer
- **ProactiveToast** - Toast notifications for new messages

#### UI Components (MUI + Radix UI)
- **Accordion** - Collapsible sections
- **AlertDialog** - Confirmation dialogs
- **Avatar** - User/companion avatars
- **Badge** - Status indicators
- **Button** - Styled buttons
- **Card** - Content containers
- **Dialog** - Modals
- **DropdownMenu** - Context menus
- **Input** - Form inputs
- **Label** - Form labels
- **Select** - Dropdown selection
- **Slider** - Range sliders
- **Switch** - Toggle switches
- **Tabs** - Tab navigation
- **Tooltip** - Hover information

#### Manga Components (Special Feature)
- **CharacterExpression** - Manga-style character expressions
- **ComicPanel** - Comic panel renderer
- **ComicSFX** - Sound effects
- **MangaBubble** - Speech bubbles
- **MangaDemo** - Demo page

---

### State Management (Zustand)

**Main Store** (`store.ts` - 1008 lines):

```typescript
interface AppState {
  user: { name: string; email: string } | null;
  authToken: string | null;
  refreshToken: string | null;
  companions: Companion[];
  myCompanions: Companion[];
  messages: Message[];
  
  // Actions
  login(name, email): void;
  authLogin(email, password): Promise<{success, message}>;
  authRegister(name, email, password): Promise<{success, message, userId}>;
  authVerifyOtp(email, otp): Promise<{success, message}>;
  authResendOtp(email): Promise<{success, message}>;
  logout(): void;
  selectCompanion(id, newName): void;
  updateCompanionAvatar(id, url): void;
  sendMessage(id, text): Promise<void>;
  rateMessage(id, rating): void;
  addSystemMessage(id, text): void;
  addXp(id, amount): void;
  unlockNextLevel(id): Promise<void>;
  startScenario(id, scenarioId, title): void;
  maybeAbandonScenario(id): void;
  deleteCompanion(id): Promise<void>;
}
```

**Persistence**: `localStorage` with `zustand/middleware/persist`

**Auth Headers Generation**:
```typescript
function authHeaders(): Record<string, string> {
  const token = useStore.getState().authToken;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
```

**Token Refresh**:
```typescript
async function refreshAccessToken(): Promise<boolean> {
  // Calls /auth/refresh endpoint
  // Updates store on success
  // Returns false on failure
}
```

---

### Routing Structure

```typescript
createBrowserRouter([
  { path: "/", element: <Landing /> },
  {
    element: <AuthLayout />,
    children: [
      { path: "login", element: <Login /> },
      { path: "signup", element: <Signup /> },
      { path: "verify-email", element: <VerifyEmail /> },
      { path: "forgot-password", element: <ForgotPassword /> },
    ]
  },
  { path: "select", element: <CompanionSelection /> },
  { path: "upgrade", element: <Payment /> },
  {
    path: "app",
    element: <ProtectedRoute />,  // Checks authToken
    children: [
      { index: true, element: <Dashboard /> },
      { path: "chat/:id", element: <Chat /> },
      { path: "companion/:id/profile", element: <CompanionProfilePage /> },
      { path: "companion/:id/episodes", element: <EpisodesListPage /> },
      { path: "companion/:id/episodes/play/:episodeId", element: <EpisodePlayer /> },
      { path: "companion/:id/journal", element: <JournalPage /> },
      { path: "quests", element: <QuestsPage /> },
      { path: "campus-lounge", element: <GroupChatPage /> },
      { path: "study-room", element: <StudyRoomPage /> },
      { path: "me", element: <UserProfile /> },
      // ... more settings pages
    ]
  }
])
```

---

### Form Handling & Validation

**Framework**: `react-hook-form` v7.55.0

**Validation Approach**:
- **Client-side**: react-hook-form with Yup or built-in validators
- **Server-side**: Pydantic models in backend
- **Email**: Format validation (EmailStr)
- **Password**: Complexity requirements (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char)
- **OTP**: 6-digit validation
- **Rate limiting**: Prevents brute force

**Example (Login)**:
```typescript
const { register, handleSubmit, errors } = useForm();
const onSubmit = handleSubmit(async (data) => {
  const result = await authLogin(data.email, data.password);
  if (result.success) {
    // Redirect to dashboard
  }
});
```

---

## 7. AUTHENTICATION & AUTHORIZATION

### Registration Flow
1. User submits `email`, `full_name`, `password`
2. Server validates password complexity
3. Server creates user in database (status: not verified)
4. Server generates 6-digit OTP with pepper + bcrypt
5. Server sends OTP email (optional - can proceed without verification)
6. User receives OTP email
7. User verifies OTP by entering code
8. User's `is_verified` flag becomes `true`
9. User can now log in

**Security Features**:
- Timing-constant response to prevent user enumeration
- Account lockout after 5 failed login attempts (30 min)
- Password hashing with bcrypt (12 rounds)
- Rate limiting: 5 login attempts per 15 min per email

---

### Login Flow
1. User submits `email`, `password`
2. Server checks account lockout status
3. Server verifies account is verified
4. Server validates password with bcrypt
5. If valid:
   - Generate access token (15 min expiry)
   - Generate refresh token (7 day expiry)
   - Update `last_login` timestamp
   - Return tokens + user profile
6. If invalid:
   - Increment failed login attempts
   - Lock account if threshold exceeded
   - Return error

**Token Structure** (JWT payload):
```json
{
  "user_id": "string",
  "email": "user@example.com",
  "role": "user",
  "jti": "unique_token_id",
  "family": "access:userid:timestamp",
  "exp": "2024-08-09T10:30:00Z",
  "iat": "2024-08-09T10:15:00Z",
  "type": "access"
}
```

---

### Token Refresh Flow
1. Client receives `401 Unauthorized` error
2. Client calls `/auth/refresh` with refresh token
3. Server validates refresh token:
   - Checks token type is "refresh"
   - Checks token is not blacklisted
   - Verifies user still exists and is active
4. If valid:
   - Adds old token to revoked_tokens collection (TTL: 7 days)
   - Generates new access_token
   - Generates new refresh_token with new JTI
   - Returns both tokens
5. If invalid:
   - Returns 401 error
   - Client clears auth state and redirects to login

**Security Features**:
- Token rotation (old tokens invalidated on refresh)
- Token family tracking for revocation
- Refresh tokens expire in 7 days

---

### Logout Flow
1. Client calls `/auth/logout` with access token
2. Server decodes token to get JTI
3. Server adds token JTI to token_blacklist collection
4. Token automatically expires from cache
5. Client clears auth tokens from localStorage

**Revocation Time**: Access tokens expire in 15 min, so logout is almost immediate

---

### Protected Routes
```typescript
function ProtectedRoute() {
  const authToken = useStore(state => state.authToken);
  if (!authToken) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
```

**Middleware Check** (Backend):
```python
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    # 1. Verify token is provided
    # 2. Decode JWT
    # 3. Check token is not blacklisted
    # 4. Get user from database
    # 5. Verify user is active
    # 6. Verify user is verified
    # 7. Verify user is not locked
```

**Error Response**:
```json
{
  "success": false,
  "error_code": "AUTH_002",
  "message": "Email not verified. Please verify your email to continue.",
  "request_id": "abc123"
}
```

---

### Role-Based Access Control (RBAC)
- **USER**: Default role for all users
- **ADMIN**: Admin users (placeholder, not implemented)
- **MODERATOR**: Moderator role (placeholder, not implemented)

**Role Checking** (Backend):
```python
class RequireRole:
    def __init__(self, *roles: UserRole):
        self.roles = roles
    
    async def __call__(self, user: UserInDB = Depends(get_current_user)):
        if user.role not in self.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions"
            )
        return user

RequireAdmin = RequireRole(UserRole.ADMIN)
RequireModerator = RequireRole(UserRole.ADMIN, UserRole.MODERATOR)
```

---

## 8. THIRD-PARTY INTEGRATIONS

### OpenRouter API
**Purpose**: AI model inference for companion responses

**Configuration**:
```python
openrouter_api_key=your-key
openrouter_http_referer=https://yourdomain.com
openrouter_x_title=AI Campus Companion
openrouter_base_url=https://openrouter.ai/api/v1
```

**Models by Companion**:
| Companion | Model |
|-----------|-------|
| Julian (philosopher) | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Victoria (rival) | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Oliver (study_buddy) | `meta-llama/llama-3.3-70b-instruct:free` |
| Chloe (party_friend) | `google/gemma-4-31b-it:free` |
| Toby (freshman) | `openai/gpt-oss-20b:free` |
| Default | `openai/gpt-4o-mini` |

**Embedding Model**: `openai/text-embedding-3-small` (for memory search)

**API Calls**:
- `POST /chat/completions` - Generate companion replies
- `POST /embeddings` - Generate vector embeddings for memories

**Usage Example**:
```python
from app.services.openrouter_client import generate_reply

reply = await generate_reply(
    messages=[
        {"role": "system", "content": "You are Oliver..."},
        {"role": "user", "content": "Hello!"}
    ],
    model="meta-llama/llama-3.3-70b-instruct:free"
)
```

---

### MongoDB
**Purpose**: Document database for user data, sessions, memories, etc.

**Configuration**:
```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ai_campus
```

**Connection Options** (from config.py):
- `maxPoolSize: 50`
- `minPoolSize: 10`
- `serverSelectionTimeoutMS: 5000`
- `connectTimeoutMS: 5000`
- `socketTimeoutMS: 30000`

**Persistence**: Runs without MongoDB in development (uses in-memory fallback)

---

### Gmail SMTP
**Purpose**: Send OTP emails and password reset emails

**Configuration**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password  # 16-character app password
SMTP_FROM_NAME=AI Campus Companion
SMTP_FROM_EMAIL=noreply@aicampus.com
```

**Email Types Sent**:
- Registration OTP (10 min expiry)
- Password reset OTP (10 min expiry)
- Welcome email (optional)

**Security**:
- Uses Gmail App Passwords (not raw password)
- OTP hashing with pepper + bcrypt
- Rate limiting on OTP requests (3 per hour)

---

### External Services (None Active)
- **Payment Gateway**: Placeholder page only
- **Analytics**: None configured
- **Social Login**: None configured
- **Map Services**: None configured
- **Cloud Storage**: None configured

---

## 9. ENVIRONMENT VARIABLES & CONFIGURATION

### Required Environment Variables

#### Application Settings
```bash
APP_NAME="AI Campus Companion"
APP_ENV="development"  # or "production"
DEBUG=true  # or false
```

#### MongoDB Configuration
```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ai_campus
```

#### JWT Authentication
```bash
SECRET_KEY=your-super-secure-random-secret-key-min-32-characters-long-change-this
  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### SMTP/Email Configuration
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_NAME=AI Campus Companion
SMTP_FROM_EMAIL=noreply@aicampus.com
```

#### Rate Limiting Configuration
```bash
RATE_LIMIT_LOGIN_MAX=5  # Maximum login attempts per 15 min
RATE_LIMIT_LOGIN_WINDOW=900  # 15 minutes in seconds

RATE_LIMIT_OTP_RESEND_MAX=3  # Maximum OTP resends per hour
RATE_LIMIT_OTP_RESEND_WINDOW=3600  # 1 hour in seconds

RATE_LIMIT_GENERAL_MAX=100  # General API calls per 60 sec
RATE_LIMIT_GENERAL_WINDOW=60  # 60 seconds
```

#### CORS Configuration
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5179,http://localhost:5180,http://localhost:5181
CORS_ALLOW_CREDENTIALS=true
```

#### Security Configuration
```bash
BCRYPT_ROUNDS=12
MAX_MESSAGE_LENGTH=10000
ACCOUNT_LOCKOUT_MINUTES=30
MAX_FAILED_LOGINS=5
```

#### OpenRouter API Configuration
```bash
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_HTTP_REFERER=https://yourdomain.com
OPENROUTER_X_TITLE=AI Campus Companion
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
```

#### Companion Configuration
```bash
TRAINABLE_COMPANIONS=philosopher,rival
DEMO_COMPANIONS=study_buddy,party_friend,freshman

COMPANION_MODELS={
  "philosopher": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "rival": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "study_buddy": "meta-llama/llama-3.3-70b-instruct:free",
  "party_friend": "google/gemma-4-31b-it:free",
  "freshman": "openai/gpt-oss-20b:free"
}
```

#### RL Training Configuration
```bash
RL_TRAINING_INTERVAL_MINUTES=60
RL_MIN_TRANSITIONS_FOR_TRAINING=50
```

#### Data Management
```bash
RESET_LOCAL_DATA_ON_STARTUP=false
```

---

### Config File Structure

`backend/app/config.py` uses Pydantic Settings:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore",
    )

    app_name: str
    app_env: str
    debug: bool
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    # ... more settings
```

**Access Pattern**:
```python
from app.config import get_settings
settings = get_settings()
secret_key = settings.secret_key
```

---

### Environment Variants

#### Development
- `APP_ENV=development`
- `DEBUG=true`
- `CORS_ORIGINS` includes all localhost ports
- MongoDB runs locally

#### Production
- `APP_ENV=production`
- `DEBUG=false`
- `CORS_ORIGINS` only includes production domains
- **Security**: Validates CORS doesn't include localhost
- Rate limits enforce strict boundaries
- Rate limit headers included in responses

---

## 10. DEPLOYMENT & DEVOPS

### Development Setup

**Backend Prerequisites**:
```bash
# Install Python 3.10+
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt
```

**Frontend Prerequisites**:
```bash
# Install Node.js 18+
cd frontend
npm install
```

**Running the App**:
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Environment Setup**:
```bash
cp backend/.env.example backend/.env
# Edit .env with your values
```

**Database Setup**:
- Start MongoDB locally or use MongoDB Atlas
- Default URI: `mongodb://localhost:27017`

---

### Production Deployment

**Backend Deployment**:
```bash
# Build and start with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Use Gunicorn for production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend Deployment**:
```bash
# Build production assets
npm run build

# Deploy dist/ folder to any static host
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Nginx
```

---

### Docker Deployment

**Note**: No Dockerfile found in repo, but deployment could be containerized:

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - mongo

  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - backend

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

---

### CI/CD (Not Found)

No CI/CD configuration found in repository:
- No `.github/workflows/` directory
- No GitLab CI configuration
- No Jenkinsfile

**Recommended CI/CD**:
- GitHub Actions for automated testing
- Auto-deploy on main branch
- Automated linting and formatting (black, flake8, mypy)
- Docker image build and push to registry

---

### Nginx Configuration (Recommended)

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend static files
    location /assets {
        root /var/www/frontend/dist;
    }
}
```

---

### Environment-Specific Config

**Development**:
```bash
DEBUG=true
CORS_ORIGINS=http://localhost:5173
MONGODB_URI=mongodb://localhost:27017
```

**Production**:
```bash
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ai_campus
```

---

## 11. DEPENDENCIES ANALYSIS

### Backend Dependencies (requirements.txt)

#### Production Dependencies
- **FastAPI** (0.115.6): Web framework
- **Uvicorn** (0.30.6): ASGI server
- **PyMongo Motor** (4.8.0+): Async MongoDB driver
- **Pydantic** v2: Data validation
- **Pydantic Settings** (2.6.1): Configuration management
- **PyJWT** (2.8.0): JWT tokens
- **bcrypt** (4.1.2): Password hashing
- **httpx** (0.27.2): HTTP client for OpenRouter
- **numpy** (<2.0): Numerical computing
- **pandas** (2.2.3): Data manipulation
- **scikit-learn** (>=1.3.0): ML utilities
- **FAISS-CPU** (1.13.2): Vector search
- **PyTorch** (>=2.1.0): Deep learning
- **Transformers** (>=4.35.0): Hugging Face models
- **Datasets** (>=2.14.0): Hugging Face datasets
- **APScheduler** (>=3.10.0): Background jobs
- **python-jose** (3.3.0): JWT library
- **aiosmtplib** (3.0.2): Async SMTP
- **python-dateutil** (2.9.0): Date parsing
- **tenacity** (9.0.0): Retry logic

#### Development Dependencies
- **pytest** (8.3.3): Test framework
- **pytest-asyncio** (0.24.0): Async testing
- **pytest-cov** (6.0.0): Coverage reporting
- **black** (24.10.0): Code formatter
- **flake8** (7.1.1): Linter
- **mypy** (1.13.0): Type checker
- **isort** (5.13.2): Import sorter

#### Status: **ALL UP TO DATE**

---

### Frontend Dependencies (package.json)

#### Production Dependencies
- **React** (18.3.1): UI library
- **Vite** (6.3.5): Build tool
- **Zustand** (^5.0.11): State management
- **React Router** (7.13.0): Routing
- **Axios** (^1.18.1): HTTP client
- **Material-UI** (7.3.5): Component library
- **Radix UI** (various): Accessible primitives
- **Tailwind CSS** (4.1.12): Styling
- **Emotion** (11.14.0): CSS-in-JS
- **Motion** (12.23.24): Animations
- **Recharts** (2.15.2): Charts
- **Lucide React** (0.487.0): Icons
- **date-fns** (3.6.0): Date utilities
- **react-hook-form** (7.55.0): Forms
- **react-dnd** (16.0.1): Drag and drop
- **canvas-confetti** (^1.9.4): Effects
- **sonner** (2.0.3): Toasts

#### Development Dependencies
- **@vitejs/plugin-react** (4.7.0): React plugin
- **@tailwindcss/vite** (4.1.12): Tailwind Vite plugin
- **TypeScript** (implicitly via .ts files)

#### Peer Dependencies
- **React** (18.3.1) - Optional (but used)
- **React DOM** (18.3.1) - Optional (but used)

#### Status: **ALL UP TO DATE**

---

### Package Health Check

#### Outdated Packages
- **None detected** in requirements.txt or package.json

#### Deprecated Packages
- **None detected**

#### Suspicious Packages
- **None detected**

#### Potential Issues
- **numpy < 2.0**: Good - numpy 2.0 may have breaking changes
- **Python version unspecified**: Should specify minimum 3.10

---

## 12. BUSINESS LOGIC & WORKFLOWS

### Core User Flows

#### Flow 1: User Registration & Verification
```
1. User navigates to /signup
2. User enters email, full_name, password
3. Server validates password (8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 special char)
4. Server creates user in database (is_verified=false, failed_login_attempts=0)
5. Server generates 6-digit OTP
6. Server sends OTP email (Gmail SMTP)
7. User receives OTP in email
8. User enters OTP on /verify-email page
9. Server verifies OTP (checks expiry, attempts, uses pepper + bcrypt)
10. Server updates user.is_verified = true
11. User redirected to /companion-selection
12. User selects first companion
13. Server stores active scenario in memory
14. User can start chatting
```

---

#### Flow 2: User Login
```
1. User navigates to /login
2. User enters email, password
3. Server checks rate limit (5 attempts per 15 min)
4. Server verifies account exists and is verified
5. Server checks if account is locked
6. Server validates password with bcrypt
7. If valid:
   a. Generate JWT access_token (15 min expiry)
   b. Generate JWT refresh_token (7 day expiry)
   c. Update user.last_login
   d. Return tokens + user profile
8. If invalid:
   a. Increment failed_login_attempts
   b. If >=5 attempts, lock account for 30 min
   c. Return error
9. Client stores tokens in localStorage
10. Client redirects to /app
```

---

#### Flow 3: Sending a Message
```
For Demo Companions (Oliver, Chloe, Toby):

1. User types message in chat input
2. Client calculates XP delta locally:
   a. Check message length
   b. Check for toxic words (-5 XP)
   c. Check for break-immersion phrases (-2 XP)
   d. Check for spam repetition (-1 XP)
   e. Check for low effort (<2 chars) (-1 XP)
   f. If active scenario + 8+ chars: +15 XP
   g. If 25+ chars: +12 XP
   h. If 8-25 chars: +10 XP
3. Client calls POST /api/chat
4. Server validates auth token
5. Server gets conversation history (last 50 messages)
6. Server constructs prompt with system prompt + conversation + user message
7. Server calls OpenRouter API with appropriate model
8. Server receives AI response
9. Server stores message in conversation_sessions
10. Server returns response + XP delta
11. Client displays response + XP message
12. Client updates local state with new XP

For Trainable Companions (Julian, Victoria):

1. User types message in chat input
2. Server validates auth token
3. Server tracks quest progress (companion message count)
4. Server gets conversation history (last 50 messages)
5. Server evaluates XP delta:
   a. Analyzes message for toxicity, effort, context
   b. Returns XP delta + reasons
6. Server retrieves relevant memories via semantic search (FAISS)
7. Server builds prompt with:
   a. System prompt
   b. Conversation history
   c. User message
   d. Retrieved memories
   e. Relationship stage
   f. XP/level information
   g. RL action (trainable only)
8. Server calls OpenRouter API with companion-specific model
9. Server stores message + XP in conversation_sessions
10. Server stores RL transition for offline training:
    a. Current conversation state
    b. Selected RL action
    c. Received reward (XP delta)
    d. Next conversation state
11. Server updates user companion progression:
    a. relationship_points += XP_delta
    b. level calculation (100 * 1.5^(level-1) to next level)
    c. relationship_stage update
    d. pending_level_up flag
12. Server checks if relationship_stage increased
13. If yes, generate missing journals up to new stage
14. Server returns response + XP + level + relationship_stage
15. Client displays response + XP message
16. Client updates local state with new XP, level, stage
```

---

#### Flow 4: Companion Level Up
```
1. User has pending_level_up = true (XP >= next level threshold)
2. User views companion profile or chat
3. Companion shows "Level Up Available" indicator
4. User clicks "Unlock Level" button
5. Client calls POST /api/companion/{id}/unlock-level
6. Server validates pending_level_up is true
7. Server increments companion level
8. Server resets XP to 0 for new level
9. Server clears pending_level_up flag
10. Server updates progression in database
11. Server returns new level
12. Client updates local state with new level
13. Client unlocks new episodes based on level (if any)
```

---

#### Flow 5: Quest Generation & Completion
```
Daily Quest Generation (Scheduled job, 6:00 AM):

1. Job calls QuestService.generate_all_daily_quests()
2. Job gets all active users
3. For each user:
   a. Check if user already has active quests today
   b. If not, generate 5 daily quests:
      - 2 chat quests (first message, 10 messages)
      - 2 lounge quests (join chat, 5 messages)
      - 1 study quest (30 minutes)
   c. Insert quests into user_quests collection
4. Return count of quests generated

Quest Completion:

1. User clicks "Complete" on quest
2. Client opens modal with text input
3. User enters report: "I sent 10 messages to Oliver today!"
4. Client calls POST /api/quests/complete/{quest_id}
5. Server validates quest is active
6. Server gets companion info
7. Server sends report to OpenRouter for verification
8. If verified:
   a. Mark quest as completed
   b. Award XP via XP evaluator
   c. Add RL transition with reward=5.0
   d. Return success message
9. If not verified:
   a. Increment retry_count
   b. Allow one more attempt
   c. Return error message
10. Client displays success/error
11. Client updates quest status locally
12. If completed, show celebration confetti
```

---

#### Flow 6: Journal Generation
```
1. User's relationship_stage increases (e.g., Stranger → Curious)
2. Server detects stage increase (via XP update)
3. Server calls JournalService.check_and_generate_journals()
4. For each missing stage (0 to new_stage):
   a. Get last 20 messages from conversation history
   b. Get user's name and companion info
   c. Build prompt for OpenRouter:
      - Persona description
      - Relationship stage
      - Recent conversation context
      - Writing style guidelines
   d. Call OpenRouter to generate 2-3 sentence entry
   e. Clean up response
   f. Save journal entry to database
   g. Set is_unlocked=true if stage <= current_stage
5. Journals automatically generated daily at 2 AM for all users
```

---

#### Flow 7: Proactive Messaging
```
Scheduling (Every 6 hours):

1. Job calls ProactiveService.schedule_triggers()
2. For each active user:
   a. Check if good morning is due (8 AM local time)
   b. Check if miss_you is due (2 days of inactivity)
   c. Check if milestone congrats is due (relationship milestones)
   d. Check if quest reminder is due (30 min after quest creation)
   e. Check if story nudge is due (user hasn't interacted with episodes)
   f. Create trigger document in proactive_triggers
   g. Store scheduled_at, context

Processing (Every 30 minutes):

1. Job calls ProactiveService.process_triggers()
2. For each pending trigger:
   a. If GOOD_MORNING: generate "Good morning! ☀️"
   b. If MISS_YOU: generate "Thinking of you!"
   c. If MILESTONE_CONGRATS: generate based on relationship stage
   d. If QUEST_REMINDER: generate reminder about pending quests
   e. If STORY_NUDGE: generate "Want to continue the story?"
   f. Call OpenRouter with prompt
   g. Generate message content
   h. Save to companion_initiated_messages
   i. Mark trigger as processed
   j. Send email to user (optional)

User Interaction:

1. User views Dashboard or Chat
2. Notification bell shows unread count
3. User clicks notification
4. Proactive message appears in chat
5. User can reply or mark as read
6. Marking as read stores read_at timestamp
```

---

#### Flow 8: Study Session
```
1. User navigates to /app/study-room
2. User sets duration (e.g., 25 minutes)
3. User optionally enters focus topic (e.g., "Calculus")
4. User clicks "Start Session"
5. Client calls POST /api/study/sessions
6. Server creates study session:
   a. Set status="active"
   b. Calculate expected_end_at = now + duration_minutes
   c. Save to study_sessions collection
   d. Return session details
7. Client starts timer with countdown
8. Timer ticks every second
9. User works on study task
10. Server tracks time via heartbeat endpoint (optional)
11. User completes session:
    a. Client calls POST /api/study/sessions/{id}/complete
    b. Server calculates XP:
       - Base: 10 XP
       - Duration bonus: 1 XP per minute
       - Interruption penalty: -5 XP per interruption
       - Minimum: 5 XP
    c. Generate congratulations message
    d. Set status="completed"
    e. Update xp_earned
    f. Return session details
12. Client shows XP earned and congratulatory message
13. Client stops timer
```

---

### Complex Algorithms

#### XP Evaluation Algorithm

```python
def evaluate_xp(text: str, recent_user_messages: List[str], has_active_scenario: bool):
    normalized = normalizeUserText(text)
    reasons = []

    # Low effort detection
    lowEffortSet = {'ok', 'k', 'kk', 'hmm', 'ya', 'yes', 'no', 'lol', 'idk', 'sure'}
    isLowEffort = len(normalized) <= 2 or (normalized in lowEffortSet and len(normalized.split(' ')) <= 2)
    if isLowEffort:
        reasons.append('low effort')

    # Toxic word detection
    toxicWords = ['stupid', 'idiot', 'dumb', 'hate you', 'kill yourself', 'moron']
    isToxic = any(w in normalized for w in toxicWords)
    if isToxic:
        reasons.append('toxic')

    # Break immersion detection
    breakPhrases = ["you're just an ai", 'this is fake', 'not real']
    isBreaksImmersion = any(p in normalized for p in breakPhrases)
    if isBreaksImmersion:
        reasons.append('breaks immersion')

    # Spam detection
    recent = [normalizeUserText(m) for m in recent_user_messages]
    isSpamRepeat = len(recent) >= 3 and all(m == normalized for m in recent[:3])
    if isSpamRepeat:
        reasons.append('spam repeat')

    # Calculate delta
    delta = 0
    if isToxic:
        delta -= 5
    if isBreaksImmersion:
        delta -= 2
    if isSpamRepeat:
        delta -= 1
    if isLowEffort and not isToxic:
        delta -= 1

    if delta == 0:
        if hasActiveScenario and len(normalized) >= 8:
            delta += 15
            reasons.append('story interaction')
        elif len(normalized) >= 25:
            delta += 12
            reasons.append('thoughtful')
        elif len(normalized) >= 8:
            delta += 10

    return max(-5, min(delta, 15)), reasons
```

---

#### Relationship Stage Calculation

```python
def get_relationship_stage(points: int) -> str:
    if points >= 500:
        return 'Confidant'
    if points >= 300:
        return 'Close Friend'
    if points >= 150:
        return 'Friend'
    if points >= 50:
        return 'Curious'
    return 'Stranger'
```

---

#### Level Calculation

```python
def _xp_for_next_level(level: int) -> int:
    # XP formula: 100 * 1.5^(level-1)
    return int(100 * (1.5 ** (level - 1)))

def calculate_level(xp: int, current_level: int) -> int:
    xp_needed = _xp_for_next_level(current_level)
    if xp >= xp_needed:
        return calculate_level(xp - xp_needed, current_level + 1)
    return current_level
```

---

#### Quest Verification Algorithm

```python
async def _verify_quest_report(companion, quest, report_text):
    prompt = f"""Verify if the user completed the following quest:

QUEST: {quest.title} - {quest.description}
COMPANION: {companion.get('name')}

USER REPORT: {report_text}

Answer YES if the report convincingly demonstrates completion, NO if not.
Provide brief reasoning."""

    try:
        response = await generate_reply(
            messages=[{"role": "user", "content": prompt}],
            model=companion.get("model", "openai/gpt-4o-mini")
        )

        # Parse response (simplified - in production use structured output)
        response_lower = response.lower()
        is_verified = 'yes' in response_lower or 'true' in response_lower

        return is_verified
    except Exception as e:
        logger.error(f"Quest verification failed: {e}")
        return False  # Fail safe: require manual review
```

---

### Business Rules & Validations

#### Registration Rules
- Password must be 8-128 characters
- Password must contain at least 1 uppercase letter
- Password must contain at least 1 lowercase letter
- Password must contain at least 1 number
- Password must contain at least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- Email must be valid format
- Username must be unique
- Rate limit: 5 registrations per IP per 15 min

#### Login Rules
- Max 5 failed attempts per 15 min per email
- Account locks for 30 min after 5 failed attempts
- Account must be verified to login
- Access token expires in 15 min
- Refresh token expires in 7 days

#### Chat Rules
- Max 30 messages per hour per user (rate limit)
- Max message length: 10,000 characters
- XSS sanitization on all messages
- Toxic word filtering (-5 XP)
- Message history stored per companion (last 50 messages)
- Demo companions use client-side XP, trainable use server-side

#### Quest Rules
- 5 daily quests generated at 6:00 AM
- 2 chat quests, 2 lounge quests, 1 study quest
- Quests auto-verify using OpenRouter
- One retry allowed per quest
- XP awarded only if verified
- Max 100 XP per day from quests

#### Study Rules
- Minimum 5 minutes, maximum 120 minutes per session
- Base XP: 10
- Duration bonus: 1 XP per minute
- Interruption penalty: -5 XP per interruption
- Minimum XP: 5 XP
- Track total focus minutes for leaderboard

---

### Notification & Email Triggers

#### Email Triggers
- **Registration OTP**: After user signs up
- **Password Reset OTP**: After user requests reset
- **Welcome Email**: Optional (can be skipped)
- **Good Morning**: 7 AM daily
- **Miss You**: After 2 days of inactivity
- **Milestone Congrats**: Relationship stage milestone
- **Quest Reminder**: 30 min after quest creation

#### In-App Notifications
- **Proactive Messages**: 5 types (good morning, miss you, milestone, quest reminder, story nudge)
- **Quest Completion**: When quest is completed
- **Level Up**: When companion level increases
- **Message Notifications**: When proactive message received
- **Toast Notifications**: Real-time alerts for new messages

---

### Payment & Subscription Logic
**Status**: Not implemented (placeholder page only)
- No Stripe/PayPal integration
- No subscription tiers
- No revenue tracking

---

## 13. SECURITY CONSIDERATIONS

### Input Validation

#### Backend Validation (Pydantic Models)
```python
class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        # ... more checks
```

#### Frontend Validation (React Hook Form)
```typescript
const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(loginSchema),
});
```

---

### File Handling & Uploads

**Status**: No file upload endpoints found
- Media endpoint exists but is likely placeholder
- No user avatar upload
- No document upload

**If Implementing File Uploads**:
- File type validation (images only)
- Size limits (e.g., 5 MB max)
- Virus scanning (external service)
- Storage path sanitization
- Prevent path traversal attacks

---

### CORS Policy

**Current Config**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers + ["*"],
)
```

**Development Origins**: `http://localhost:*, http://localhost:3000, http://localhost:5173, http://localhost:5174, http://localhost:5175, http://localhost:5179, http://localhost:5180, http://localhost:5181`

**Production**: Validates that no localhost origins are present

**Risk**: If `.env` has incorrect origins in production, security vulnerability exists

---

### Rate Limiting

**Implementation**: Custom rate limiter in `backend/app/utils/rate_limiter.py`

**Types**:
- Login rate limit: 5 attempts per 15 min per email
- OTP resend rate limit: 3 attempts per hour per email
- General API rate limit: 100 requests per 60 sec
- Chat rate limit: 30 messages per hour per user

**Mechanism**:
- Stores rate limit data in MongoDB (TTL: 1 hour)
- Tracks IP and email
- Returns X-RateLimit-* headers in responses

**Security Benefit**: Prevents brute force attacks, DDoS, and API abuse

---

### Data Sanitization

#### Email Masking
```python
def mask_email(email: str) -> str:
    local, domain = email.split('@')
    if len(local) <= 3:
        return local[0] + '***' + domain[-3:]
    return local[:3] + '***' + domain[-3:]
# Example: "user@example.com" → "use***example.com"
```

#### Input Sanitization
```python
def sanitize_input(text: str, max_length: int, allow_html: bool, check_javascript: bool) -> str:
    if len(text) > max_length:
        text = text[:max_length]
    
    if not allow_html:
        text = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    
    if check_javascript:
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text.strip()
```

---

### SQL Injection Prevention
**Not applicable** - MongoDB (NoSQL) doesn't use SQL queries
- Parameterized queries automatically prevent injection
- No raw SQL queries found in codebase

---

### XSS Prevention

#### Backend
- Message sanitization (removes HTML tags and javascript:)
- Input validation on all user inputs
- Escaping output in templates

#### Frontend
- React automatically escapes JSX
- No `dangerouslySetInnerHTML` found
- Content Security Policy (CSP) not configured (should add)

**Recommended CSP**:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; img-src 'self' data: https:;">
```

---

### CSRF Prevention
**Not implemented**
- No CSRF tokens found
- State-changing requests should include CSRF tokens

**Mitigation**: Use SameSite cookies (if cookies were used) or validate origin headers

---

### HTTPS Enforcement
**Not enforced in code**
- Development: No HTTPS required
- Production: Should force HTTPS via Nginx/Apache

**Recommended Nginx Config**:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

---

### Password Security

#### Storage
- bcrypt with 12 rounds
- Salt included in hash
- Pepper included in backend config

#### Strength Requirements
- 8-128 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

#### Session Security
- Access token expires in 15 min
- Refresh token expires in 7 days
- Token rotation on refresh
- Blacklist for logout
- IP tracking (placeholder)

---

### Account Lockout

**Implementation**:
```python
async def increment_failed_login(email: str) -> Optional[datetime]:
    user = await get_user_by_email(email)
    if not user:
        return None
    
    new_attempts = user.failed_login_attempts + 1
    
    if new_attempts >= 5:  # Max 5 attempts
        locked_until = datetime.utcnow() + timedelta(minutes=30)
        await db.users.update_one(
            {"_id": user.id},
            {"$set": {"failed_login_attempts": new_attempts, "locked_until": locked_until}}
        )
        return locked_until
    
    await db.users.update_one(
        {"_id": user.id},
        {"$set": {"failed_login_attempts": new_attempts}}
    )
    return None
```

**Policy**: 30 minute lockout after 5 failed attempts

---

### JWT Security

#### Token Structure
- Signed with HMAC-SHA256 (HS256)
- Includes user_id, email, role, jti, exp, iat
- Includes token family for rotation

#### Token Rotation
```python
async def refresh_token():
    # 1. Decode old refresh token
    # 2. Check if blacklisted
    # 3. Add old token to revoked_tokens
    # 4. Generate new access_token
    # 5. Generate new refresh_token
    # 6. Return both
```

#### Blacklist
- Stored in MongoDB with TTL
- Stored by JTI (JWT ID)
- Automatically expires with token

---

### Logging & Monitoring

**Logging Implementation**:
```python
logger.info("User logged in", extra={"email": mask_email(email), "user_id": str(user.id)})
logger.error("Error occurred", extra={"request_id": request_id}, exc_info=True)
```

**Security Logging**:
- Failed login attempts logged
- Token refresh events logged
- Rate limit breaches logged
- Request IDs tracked for debugging

**Security Best Practices**:
- Mask sensitive data (passwords, emails)
- Include stack traces in error logs
- Mask API keys in logs

---

## 14. KNOWN ISSUES & TECH DEBT

### TODO Comments

**Not found** in the codebase (grep didn't find any)

---

### FIXME Markers

**Not found** in the codebase

---

### HACK Markers

**Not found** in the codebase

---

### Hardcoded Values

#### Password Pepper
```python
otp_pepper: str = "rrdVtjVqFT3TImlRfEYoC1l93QhxqDpGL7cPxIowuoWs5b_z_tU0w2rCIDxwW8hs"
```
**Issue**: Pepper is in the source code
**Risk**: Anyone can clone repo and get the pepper
**Recommendation**: Move to environment variable or secret manager

---

#### CORS Origins
```python
cors_allow_origins: list[str] = ["http://localhost:*", "http://localhost:3000", ...]
```
**Issue**: All localhost ports hardcoded
**Risk**: Can't easily change without editing code
**Recommendation**: Use environment variable with comma-separated values

---

#### Test Endpoints
```python
@router.post("/quests/generate")  # Manually generate quests
@router.get("/health")  # Health check
```
**Issue**: Endpoints for testing only
**Risk**: May be accidentally exposed in production
**Recommendation**: Add `@app.get("/api/health")` for all environments, remove test endpoints

---

#### Undefined Behavior
**None documented**, but some areas are unclear:

1. **RL Training**: Disabled but code exists
   - `rl_worker_available = False`
   - Comment: "RL worker not available - skipping torch imports"
   - Concern: What happens when re-enabled?

2. **Media Endpoint**: Empty route file
   - `backend/app/api/media.py` exists but has no routes
   - Concern: What's the plan for media handling?

3. **Payment Page**: Placeholder only
   - `/app/upgrade` just shows static page
   - No actual payment logic
   - Concern: When implementing payments?

4. **Manga Components**: Experimental
   - Special manga rendering components
   - Likely for future feature
   - Concern: Not documented

---

### Circular Dependencies

**Not detected** in code analysis
- All imports appear to be forward-only
- No recursive imports found

---

### Code Smells

#### 1. Duplicate Code

**Issue**: Token refresh logic duplicated in frontend and backend
- Frontend: `refreshAccessToken()` in store.ts (lines 174-211)
- Backend: `/auth/refresh` endpoint
- **Recommendation**: Centralize refresh logic

---

#### 2. Magic Numbers

**Issue**: Hardcoded values scattered throughout
```python
max_failed_logins = 5
account_lockout_minutes = 30
xp_thresholds = [50, 150, 300, 500]
QUEST_TEMPLATES = [...]
```
**Recommendation**: Extract to configuration constants

---

#### 3. Inconsistent Error Handling

**Issue**: Mix of exceptions
- `AppException` (custom)
- `HTTPException` (FastAPI)
- Regular exceptions
**Recommendation**: Use only AppException throughout

---

#### 4. Large Functions

**Issue**: `_trainable_pipeline()` in `chat_routes.py` is 600+ lines
**Recommendation**: Break into smaller helper functions

---

#### 5. Missing Type Hints

**Issue**: Some functions lack type annotations
**Recommendation**: Add `mypy` strict checking

---

### Security Vulnerabilities

#### 1. Missing CSRF Protection
**Status**: Not implemented
**Risk**: Medium
**Recommendation**: Add CSRF tokens for state-changing requests

#### 2. No HTTPS Enforcement
**Status**: Not enforced in code
**Risk**: Medium
**Recommendation**: Force HTTPS in production (Nginx/Apache)

#### 3. Email in Logs
**Status**: Partially masked
**Recommendation**: Mask fully or don't log emails at all

#### 4. Exposed Password Pepper
**Status**: Found in source code
**Risk**: High
**Recommendation**: Move to environment variable

#### 5. CORS Configuration Risk
**Status**: Can accidentally include localhost in production
**Risk**: Medium
**Recommendation**: Validate CORS origins at startup

---

### Performance Concerns

#### 1. MongoDB Connection Pool
**Status**: OK (50 min pool size)
**Concern**: May need tuning for high traffic

#### 2. OpenRouter API Rate Limits
**Status**: No rate limiting implemented
**Concern**: User could spam API and get blocked
**Recommendation**: Add OpenRouter rate limiting (per user, per minute)

#### 3. Large JWT Payloads
**Status**: Reasonable (includes family, jti, etc.)
**Concern**: User IDs could be long
**Recommendation**: Use short IDs (MongoDB ObjectId is good)

#### 4. FAISS Vector Search
**Status**: Not implemented
**Concern**: Memory usage for embeddings
**Recommendation**: Test memory with real embeddings

---

### Scalability Concerns

#### 1. Single MongoDB Instance
**Status**: Not sharded
**Concern**: Will not scale horizontally
**Recommendation**: Use sharding for production

#### 2. No Caching
**Status**: No Redis or in-memory cache
**Concern**: Database queries repeated
**Recommendation**: Cache user data, quest lists, companion profiles

#### 3. Sync Session Updates
**Status**: Updates happen synchronously
**Concern**: May slow down chat responses
**Recommendation**: Queue session updates for async processing

#### 4. RL Training in Background
**Status**: Worker exists but disabled
**Concern**: Data accumulates without processing
**Recommendation**: Implement RL training pipeline

---

### Data Retention

#### TTL Collections
- `otps`: 10 min
- `token_blacklist`: Expires with token
- `rate_limits`: 1 hour
- `proactive_triggers`: 30 days
- `companion_initiated_messages`: 90 days
- `proactive_email_logs`: 30 days

**Concern**: Long TTLs may store unnecessary data
**Recommendation**: Audit and adjust TTLs

---

### Testing Coverage

**Not found**: No test files read
**Concern**: No visibility into test coverage
**Recommendation**: Add unit and integration tests

---

## 15. REPRODUCTION GUIDE

### Prerequisites

#### Backend (Python 3.10+)
```bash
# Check Python version
python --version  # Should be 3.10 or higher

# Install PostgreSQL (not used, but good to have)
# Install MongoDB (if not using Atlas)
mongod --version

# Install Git
git --version
```

#### Frontend (Node.js 18+)
```bash
# Check Node version
node --version  # Should be 18 or higher
npm --version

# Check if NPM is installed
npm -v
```

---

### Installation Steps

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd FYP-AI_Campus_Companion
```

#### Step 2: Setup Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your values (see Section 9)
nano .env  # or use any text editor
```

**Required .env Values**:
```bash
SECRET_KEY=your-32-character-secret-key-here
OPENROUTER_API_KEY=your-openrouter-api-key
MONGODB_URI=mongodb://localhost:27017
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate a Gmail app password:
1. Go to Google Account Settings
2. Security → 2-Step Verification → App passwords
3. Select "Mail" and "Other (Custom name)"
4. Copy the 16-character password

---

#### Step 3: Setup Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env (optional, mostly for API base URL)
# nano .env
```

---

#### Step 4: Setup MongoDB
**Option A: Local MongoDB**
```bash
# Install MongoDB
# Download from: https://www.mongodb.com/try/download/community

# Start MongoDB service
# On Windows:
net start MongoDB
# On macOS:
brew services start mongodb-community
# On Linux:
sudo systemctl start mongod
```

**Option B: MongoDB Atlas**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create cluster
3. Create database user
4. Get connection string
5. Update `MONGODB_URI` in `.env`

---

#### Step 5: Start Backend Server
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate

# Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Press CTRL+C to quit
INFO:     Database indexes created successfully
INFO:     All database indexes created successfully
INFO:     AI Campus Companion v2.0.0 started — trainable: ['philosopher', 'rival'], demo: ['study_buddy', 'party_friend', 'freshman']
```

---

#### Step 6: Start Frontend Server
**Open a new terminal window**:
```bash
cd frontend
npm run dev
```

**Expected output**:
```
  VITE v6.3.5  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

#### Step 7: Verify Installation
1. Open browser to http://localhost:5173
2. You should see the Landing page
3. Click "Sign Up"
4. Create an account (email: test@example.com, password: TestPass123!)
5. Check your email for OTP code
6. Enter OTP and verify
7. Select a companion
8. Start chatting!

**Test API endpoints**:
```bash
# Health check
curl http://localhost:8000/api/health

# List companions
curl http://localhost:8000/api/chat/companions
```

---

### Configuration Guide

#### Development Configuration (`.env`)
```bash
APP_NAME="AI Campus Companion"
APP_ENV="development"
DEBUG=true

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ai_campus

SECRET_KEY=your-development-secret-key-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_NAME=AI Campus Companion
SMTP_FROM_EMAIL=noreply@aicampus.com

RATE_LIMIT_LOGIN_MAX=5
RATE_LIMIT_LOGIN_WINDOW=900
RATE_LIMIT_OTP_RESEND_MAX=3
RATE_LIMIT_OTP_RESEND_WINDOW=3600
RATE_LIMIT_GENERAL_MAX=100
RATE_LIMIT_GENERAL_WINDOW=60

CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5179,http://localhost:5180,http://localhost:5181
CORS_ALLOW_CREDENTIALS=true

OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_HTTP_REFERER=http://localhost:5173
OPENROUTER_X_TITLE=AI Campus Companion
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small

TRAINABLE_COMPANIONS=philosopher,rival
DEMO_COMPANIONS=study_buddy,party_friend,freshman

RL_TRAINING_INTERVAL_MINUTES=60
RL_MIN_TRANSITIONS_FOR_TRAINING=50

RESET_LOCAL_DATA_ON_STARTUP=false
```

---

#### Production Configuration (`.env`)
```bash
APP_NAME="AI Campus Companion"
APP_ENV="production"
DEBUG=false

MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/ai_campus?retryWrites=true&w=majority
MONGODB_DB=ai_campus

SECRET_KEY=your-production-secret-key-32-chars-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_NAME=AI Campus Companion
SMTP_FROM_EMAIL=noreply@aicampus.com

RATE_LIMIT_LOGIN_MAX=5
RATE_LIMIT_LOGIN_WINDOW=900
RATE_LIMIT_OTP_RESEND_MAX=3
RATE_LIMIT_OTP_RESEND_WINDOW=3600
RATE_LIMIT_GENERAL_MAX=100
RATE_LIMIT_GENERAL_WINDOW=60

CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=true

OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_HTTP_REFERER=https://yourdomain.com
OPENROUTER_X_TITLE=AI Campus Companion
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small

TRAINABLE_COMPANIONS=philosopher,rival
DEMO_COMPANIONS=study_buddy,party_friend,freshman

RL_TRAINING_INTERVAL_MINUTES=60
RL_MIN_TRANSITIONS_FOR_TRAINING=50

RESET_LOCAL_DATA_ON_STARTUP=false
```

**Important**: In production, CORS should NOT include localhost!

---

### Special Instructions

#### 1. MongoDB Without Server
If MongoDB is not running locally:
```bash
# Option 1: Use MongoDB Atlas (recommended)
# Update MONGODB_URI in .env to Atlas connection string

# Option 2: Use in-memory mode (development only)
# The app will log "MongoDB connection failed" but continue
# Data will not persist
```

#### 2. Gmail SMTP Issues
If email sending fails:
```bash
# 1. Enable 2-Factor Authentication on your Google account
# 2. Generate an App Password:
#    - Go to Google Account Settings
#    - Security → 2-Step Verification → App passwords
#    - Select "Mail" and "Other (Custom name)"
#    - Copy the 16-character password

# 3. Use the App Password in SMTP_PASSWORD
```

#### 3. OpenRouter API Issues
If OpenRouter API fails:
```bash
# 1. Get an API key from https://openrouter.ai/
# 2. Update OPENROUTER_API_KEY in .env
# 3. Ensure you have API credits

# If no API key:
# - The app will use fallback messages
# - Demo companions will still work
# - Trainable companions may fail
```

#### 4. Port Conflicts
If ports 8000 or 5173 are in use:

**Backend**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001  # Use port 8001
```

**Frontend**:
```bash
npm run dev -- --port 5174  # Use port 5174
```

Then update the frontend API base URL:
```typescript
// frontend/src/app/store.ts
const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8001') + '/api';
```

#### 5. Windows vs macOS/Linux Paths
- Windows: Use backslashes or double backslashes: `backend\\app\\main.py`
- macOS/Linux: Use forward slashes: `backend/app/main.py`

#### 6. Virtual Environment Issues
If virtual environment fails to activate:

**Windows**:
```bash
# Delete and recreate
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux**:
```bash
# Delete and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 7. NPM Cache Issues
If npm install fails:

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules

# Delete package-lock.json
rm package-lock.json

# Reinstall
npm install
```

---

### Troubleshooting

#### Backend Won't Start
**Error**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**: Activate virtual environment and reinstall dependencies
```bash
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

---

#### Backend Won't Connect to MongoDB
**Error**: `pymongo.errors.ServerSelectionTimeoutError`
**Solution**: Start MongoDB server or use MongoDB Atlas

---

#### Frontend Won't Connect to Backend
**Error**: `Network Error` or `ERR_CONNECTION_REFUSED`
**Solution**:
1. Verify backend is running on port 8000
2. Check CORS settings
3. Check .env `VITE_API_BASE_URL`

---

#### Email Not Sending
**Error**: `smtplib.SMTPAuthenticationError`
**Solution**:
1. Check Gmail App Password
2. Enable 2-Factor Authentication
3. Check SMTP_HOST and SMTP_PORT

---

#### Companions Not Responding
**Error**: `OpenRouter API error`
**Solution**:
1. Check API key in .env
2. Verify API credits
3. Check internet connection
4. Try demo companions first

---

#### Quests Not Generating
**Solution**: Check that daily job is running (APScheduler)

---

### Development Workflow

#### Running Tests
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

---

#### Running Code Quality Checks
```bash
cd backend
source venv/bin/activate

# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Import sorting
isort app/
```

---

#### Stopping the Servers
```bash
# Press Ctrl+C in each terminal window where servers are running
```

---

### Environment Reset
If you want to reset the database and start fresh:

```bash
# Backend
cd backend
source venv/bin/activate

# Drop all collections (careful!)
mongosh ai_campus --eval "db.getCollectionNames().forEach(function(c) { db[c].drop(); })"

# Or start fresh with RESET_LOCAL_DATA_ON_STARTUP=true in .env
```

---

### Deployment Checklist

- [ ] Set production `.env` file
- [ ] Change `SECRET_KEY` to unique production key
- [ ] Update `CORS_ORIGINS` to production domains only
- [ ] Enable `DEBUG=false`
- [ ] Set up MongoDB Atlas or production MongoDB
- [ ] Get OpenRouter API key and add credits
- [ ] Set up Gmail SMTP with App Password
- [ ] Configure firewall rules (ports 8000, 443)
- [ ] Set up SSL/HTTPS certificate
- [ ] Configure Nginx or similar reverse proxy
- [ ] Set up background jobs (APScheduler needs supervision)
- [ ] Configure monitoring and logging
- [ ] Set up backups for MongoDB
- [ ] Test production deployment thoroughly
- [ ] Set up domain DNS to point to server

---

## CONCLUSION

This project specification provides a comprehensive overview of the **AI Campus Companion** application, covering all major aspects from project structure and architecture to business logic and security. The application is a well-architected full-stack React + FastAPI application with MongoDB database, featuring:

- **5 AI Companions**: Oliver, Chloe, Julian, Victoria, Toby
- **Dual-Pipeline Chat**: Trainable (RL) vs Demo (prompt-based)
- **Gamification**: XP, leveling, relationship stages, quests
- **Story Episodes**: Interactive story mode with branching choices
- **Journal System**: Private diary entries per relationship stage
- **Campus Lounge**: Group chat with companions
- **Study Room**: Pomodoro-style focus sessions
- **Proactive Messaging**: Scheduled messages based on user behavior

**Total Lines of Code**: ~9,219 lines across backend and frontend

**Tech Stack**:
- Backend: Python 3.x, FastAPI 0.115.6, MongoDB, OpenRouter API
- Frontend: React 18.3.1, Vite 6.3.5, Zustand, MUI, Tailwind CSS

**Current Status**:
- ✅ Core features implemented
- ✅ Authentication and authorization
- ✅ Chat with dual pipeline
- ✅ Quest system
- ✅ Journal system
- ✅ Study mode
- ✅ Group chat
- ⚠️ RL training disabled (placeholder)
- ❌ Payment integration (placeholder)
- ❌ Testing (no tests found)

**Next Steps**:
1. Add comprehensive test suite
2. Implement RL training pipeline
3. Add payment integration
4. Implement comprehensive monitoring
5. Add automated deployment (CI/CD)
6. Performance optimization and scaling
7. User analytics and feedback collection

---

**Document Version**: 1.0
**Last Updated**: 2024-08-08
**Generated By**: Claude (GLM-4.7 Flash)
