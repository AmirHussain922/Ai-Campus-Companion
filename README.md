# AI Campus Companion

A full-stack AI-powered campus companion application with advanced features for student interaction and personal growth.

## Features

- **AI Companions**: Interactive AI companions with distinct personalities (Oliver, Chloe, Julian, Victoria, Toby)
- **Companion Progression**: XP system, leveling, relationship stages, and companion memory
- **Companion Stories**: Unlockable episodes and storylines for each companion
- **Study Buddy System**: Match with study partners for collaborative learning
- **Peer Q&A**: Collaborative question and answer platform
- **Study Room**: Virtual study rooms with real-time messaging
- **RL-Driven Companions**: Reinforcement learning-powered companions that improve over time
- **Authentication**: Secure JWT-based authentication with email verification
- **Responsive UI**: Modern, responsive interface built with React and Tailwind CSS

## Technology Stack

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: State management
- **React Router**: Client-side routing
- **React DnD**: Drag and drop functionality

### Backend
- **FastAPI**: Python web framework
- **Python 3.12**: Runtime
- **MongoDB**: NoSQL database with Motor driver
- **APScheduler**: Background job scheduling
- **OpenRouter**: AI service integration
- **Pydantic**: Data validation

## Project Structure

```
AI_Campus_Companion/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core utilities
│   │   ├── services/     # Business logic
│   │   ├── models/       # Pydantic models
│   │   ├── memory/       # Memory management
│   │   └── companions/   # Companion system
│   ├── requirements.txt  # Python dependencies
│   ├── run_backend.py    # Backend startup script
│   └── .env.example      # Environment template
├── frontend/            # React frontend
│   ├── src/            # Source code
│   ├── package.json    # NPM dependencies
│   ├── .env.example    # Environment template
│   └── dist/           # Build output (not tracked)
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## Environment Setup

### Backend

1. Install Python 3.12 or higher
2. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment file:
   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your configuration (see below)

### Frontend

1. Install Node.js 18+ and npm/yarn/pnpm
2. Create a virtual environment:
   ```bash
   cd frontend
   pnpm install  # or npm install / yarn install
   ```

3. Copy environment file:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with your API base URL

## Configuration

### Backend (.env)

Required environment variables:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/ai_campus
MONGODB_DB=ai_campus

# JWT Authentication
SECRET_KEY=your-super-secure-random-secret-key-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP Configuration (for email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_NAME=AI Campus Companion
SMTP_FROM_EMAIL=noreply@aicampus.com

# OpenRouter API Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_HTTP_REFERER=https://yourdomain.com
OPENROUTER_X_TITLE=AI Campus Companion
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### Frontend (.env)

Required environment variables:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8002
```

## Running Locally

### Backend

```bash
cd backend
python run_backend.py
```

Backend will start on http://localhost:8002

API documentation is available at http://localhost:8002/docs

### Frontend

```bash
cd frontend
pnpm dev  # or npm run dev / yarn dev
```

Frontend will start on http://localhost:5173

## Features Overview

### AI Companions
- **Oliver** (Study Buddy): Academic partner with logical thinking
- **Chloe** (Party Co-conspirator): Energetic social butterfly
- **Julian** (Midnight Confidant): Deep thinker and philosopher
- **Victoria** (Academic Rival): Challenging and competitive
- **Toby** (Freshman Mentee): Curious and eager to learn

### Companion Progression
- XP system for interactions
- Level progression
- Relationship stages (Stranger → Curious → Friend → Close Friend → Confidant)
- Unlockable episodes and storylines

### Study Buddy System
- Match with study partners
- Real-time messaging
- Conversation history
- Buddy requests and connections

### Peer Q&A
- Ask questions to the community
- Get answers from peers
- Comment and rate answers
- Topic-specific discussions

### Study Room
- Create virtual study rooms
- Real-time chat
- Room management
- Topic-based organization

## Deployment

### Backend Deployment

1. Set environment variables in your hosting environment
2. Ensure MongoDB connection is properly configured
3. Use a process manager like Supervisor or systemd to keep it running
4. Use HTTPS for all requests

### Frontend Deployment

1. Build the production bundle:
   ```bash
   cd frontend
   pnpm build
   ```

2. Deploy the `dist/` folder to your static file server (e.g., Nginx, Apache)

3. Configure your server to proxy API requests to the backend

## License

MIT License

## Author

Amir Hussain
