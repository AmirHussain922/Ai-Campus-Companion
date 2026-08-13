"""
Study Buddy API routes for AI Campus Companion.

Provides endpoints for study buddy profiles, matching, and connections.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import json

from app.core.auth import get_current_active_user
from app.core.validation import PaginationParams
from app.models import (
    StudyBuddyProfileCreate,
    StudyBuddyProfileUpdate,
    StudyBuddyProfileResponse,
    StudyBuddyMatchRequest,
    StudyBuddyMatchResponse,
    ConnectionRequestCreate,
    ConnectionRequestResponse,
    ConnectionResponse,
    UserInDB,
    MessageCreate,
    MessageResponse,
    ConversationCreate,
    ConversationResponse,
    StudyRoomCreate,
    StudyRoomUpdate,
    StudyRoomJoinRequest,
    RoomMessageCreate,
    RoomMessageResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    AnswerCreate,
    AnswerUpdate,
    AnswerResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
)
from app.services.study_buddy_service import StudyBuddyService
from app.services.study_buddy_messaging_service import StudyBuddyMessagingService
from app.services.qa_service import QaService
from app.services.study_room_service import StudyRoomService
from app.services.study_room_messaging_service import StudyRoomMessagingService
from app.core.auth import get_current_active_user, get_current_user_id
from app.core.database import get_database, get_study_buddy_conversations_collection
from bson import ObjectId
import logging
from fastapi import WebSocket, WebSocketDisconnect, Query, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-buddy", tags=["study-buddy"])


# ============================================================================
# Profile Routes
# ============================================================================

@router.get("/profile", response_model=dict)
async def get_profile(user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user's study buddy profile.

    Creates profile if it doesn't exist.
    """
    try:
        profile = await StudyBuddyService.get_or_create_profile(str(user.id))
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "data": profile.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get profile", "error_code": "SBY_001"}
        )


@router.post("/profile", response_model=dict)
async def create_profile(
    profile_data: StudyBuddyProfileCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Create study buddy profile.

    Validates all required fields and saves to database.
    """
    try:
        # Update profile (this will create it if it doesn't exist)
        profile = await StudyBuddyService.update_profile(str(user.id), profile_data)
        return {
            "success": True,
            "message": "Profile created successfully",
            "data": profile.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_002"}
        )
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create profile", "error_code": "SBY_001"}
        )


@router.put("/profile", response_model=dict)
async def update_profile(
    profile_data: StudyBuddyProfileUpdate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Update study buddy profile.

    Partial updates allowed - only provided fields will be updated.
    """
    try:
        profile = await StudyBuddyService.update_profile(str(user.id), profile_data)
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": profile.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_002"}
        )
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update profile", "error_code": "SBY_001"}
        )


# ============================================================================
# Matching Routes
# ============================================================================

@router.get("/match", response_model=dict)
async def find_matches(
    limit: int = 20,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Find study buddy matches for the current user.

    Returns users with high compatibility scores based on:
    - Strong/weak subject compatibility
    - Same campus, major, or academic year
    - Related subjects overlap
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Limit must be between 1 and 100", "error_code": "SBY_003"}
            )

        matches = await StudyBuddyService.find_matches(str(user.id), limit=limit)
        return {
            "success": True,
            "message": f"Found {matches.total_matches} matches",
            "data": matches.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_002"}
        )
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to find matches", "error_code": "SBY_001"}
        )


# ============================================================================
# Connection Routes
# ============================================================================

@router.post("/request/send", response_model=dict)
async def send_connection_request(
    request_data: ConnectionRequestCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Send a connection request to another user.

    Validates:
    - Both users have profiles
    - Not self-request
    - No duplicate pending requests
    - Not already connected
    """
    try:
        result = await StudyBuddyService.send_connection_request(
            sender_id=str(user.id),
            recipient_id=request_data.recipient_id,
            message=request_data.message,
        )
        return {
            "success": True,
            "message": "Connection request sent successfully",
            "data": result.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Connection request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_002"}
        )
    except Exception as e:
        logger.error(f"Error sending connection request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to send connection request", "error_code": "SBY_001"}
        )


@router.get("/request/pending", response_model=dict)
async def get_pending_requests(user: UserInDB = Depends(get_current_active_user)):
    """
    Get all pending connection requests for the current user.
    """
    try:
        requests = await StudyBuddyService.get_pending_requests(str(user.id))
        return {
            "success": True,
            "message": f"Found {len(requests)} pending requests",
            "data": [r.model_dump() for r in requests],
        }
    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get pending requests", "error_code": "SBY_001"}
        )


@router.post("/request/respond", response_model=dict)
async def respond_to_request(
    request_id: str,
    action: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Respond to a connection request.

    Action must be "accept" or "reject".
    """
    try:
        # Validate action
        if action.lower() not in ["accept", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Action must be 'accept' or 'reject'", "error_code": "SBY_004"}
            )

        result = await StudyBuddyService.respond_to_request(request_id, str(user.id), action.lower())
        return {
            "success": True,
            "message": f"Request {action.lower()}ed successfully",
            "data": result.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Connection request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_002"}
        )
    except Exception as e:
        logger.error(f"Error responding to request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to respond to request", "error_code": "SBY_001"}
        )


@router.get("/connections", response_model=dict)
async def get_connections(user: UserInDB = Depends(get_current_active_user)):
    """
    Get all accepted connections for the current user.
    """
    try:
        connections = await StudyBuddyService.get_connections(str(user.id))
        return {
            "success": True,
            "message": f"Found {len(connections)} connections",
            "data": [c.model_dump() for c in connections],
        }
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get connections", "error_code": "SBY_001"}
        )


# ============================================================================
# Conversation and Messaging Routes
# ============================================================================

@router.get("/conversations", response_model=dict)
async def get_conversations(
    page: int = 1,
    per_page: int = 50,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get all conversations for the current user.
    """
    try:
        pagination = PaginationParams(limit=per_page, offset=(page - 1) * per_page)
        result = await StudyBuddyMessagingService.get_conversations(str(user.id), pagination)
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} conversations",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get conversations", "error_code": "SBY_001"}
        )


@router.post("/conversations", response_model=dict)
async def create_conversation(
    data: ConversationCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get or create a conversation with another user.
    """
    try:
        conversation = await StudyBuddyMessagingService.get_or_create_conversation(
            str(user.id),
            data.other_user_id
        )
        return {
            "success": True,
            "message": "Conversation created successfully",
            "data": conversation.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create conversation", "error_code": "SBY_001"}
        )


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get conversation details and verify user is a participant.
    """
    try:
        conversation = await StudyBuddyMessagingService.get_conversation_by_ids(conversation_id, str(user.id))
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Conversation not found", "error_code": "SBY_005"}
            )
        return {
            "success": True,
            "message": "Conversation retrieved successfully",
            "data": conversation,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get conversation", "error_code": "SBY_001"}
        )


@router.get("/conversations/{conversation_id}/messages", response_model=dict)
async def get_messages(
    conversation_id: str,
    page: int = 1,
    per_page: int = 50,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get messages for a conversation.
    """
    try:
        pagination = PaginationParams(limit=per_page, offset=(page - 1) * per_page)
        result = await StudyBuddyMessagingService.get_messages(conversation_id, str(user.id), pagination)
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} messages",
            "data": result,
        }
    except ValueError as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e), "error_code": "SBY_006"}
        )
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get messages", "error_code": "SBY_001"}
        )


@router.post("/messages", response_model=dict)
async def create_message(
    data: MessageCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Send a message to a conversation.
    """
    try:
        message = await StudyBuddyMessagingService.create_message(
            data.conversation_id,
            str(user.id),
            data.content
        )
        return {
            "success": True,
            "message": "Message sent successfully",
            "data": message.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_007"}
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to send message", "error_code": "SBY_001"}
        )


@router.post("/conversations/{conversation_id}/read", response_model=dict)
async def mark_as_read(
    conversation_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Mark all messages in a conversation as read for the current user.
    """
    try:
        count = await StudyBuddyMessagingService.mark_messages_as_read(conversation_id, str(user.id))
        return {
            "success": True,
            "message": f"Marked {count} messages as read",
            "data": {"messages_read": count},
        }
    except ValueError as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e), "error_code": "SBY_006"}
        )
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to mark messages as read", "error_code": "SBY_001"}
        )


@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Delete a conversation and all its messages.
    """
    try:
        success = await StudyBuddyMessagingService.delete_conversation(conversation_id, str(user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Conversation not found", "error_code": "SBY_005"}
            )
        return {
            "success": True,
            "message": "Conversation deleted successfully",
            "data": {},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete conversation", "error_code": "SBY_001"}
        )


# ============================================================================
# WebSocket Real-Time Messaging
# ============================================================================


class ConnectionManager:
    """Manage WebSocket connections for real-time messaging."""

    def __init__(self):
        # Dictionary: conversation_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Dictionary: conversation_id -> set of user IDs
        self.conversation_participants: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
            self.conversation_participants[conversation_id] = set()
        self.active_connections[conversation_id].append(websocket)
        self.conversation_participants[conversation_id].add(user_id)

    def disconnect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Remove a WebSocket connection."""
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
            self.conversation_participants[conversation_id].discard(user_id)
            if not self.conversation_participants[conversation_id]:
                del self.conversation_participants[conversation_id]

    async def broadcast(
        self,
        conversation_id: str,
        message: dict,
        exclude_socket: Optional[WebSocket] = None
    ):
        """Broadcast a message to all participants in a conversation."""
        if conversation_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[conversation_id]:
            try:
                if exclude_socket and connection == exclude_socket:
                    continue
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error in broadcast to connection: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for connection in dead_connections:
            if connection in self.active_connections.get(conversation_id, []):
                self.active_connections[conversation_id].remove(connection)


        # Clean up empty lists
        if conversation_id in self.active_connections and not self.active_connections[conversation_id]:
            del self.active_connections[conversation_id]
        if conversation_id in self.conversation_participants and not self.conversation_participants[conversation_id]:
            del self.conversation_participants[conversation_id]


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str = Query(..., description="Conversation ID"),
    token: str = Query(..., description="JWT Access Token")
):
    """
    WebSocket endpoint for real-time messaging.

    Connect with:
    - Authorization: JWT Bearer token (passed as query parameter for compatibility)
    - Query params: conversation_id, token

    This WebSocket requires users to be connected Study Buddies before messaging.
    """
    print(f"DEBUG: websocket_endpoint called for conversation_id={conversation_id}", flush=True)
    logger.info(f"DEBUG: websocket_endpoint called for conversation_id={conversation_id}")

    # Extract user_id from JWT token
    try:
        print(f"DEBUG: Starting authentication", flush=True)
        logger.info(f"DEBUG: Starting authentication")
        user_id = get_current_user_id(token)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    # Verify user exists
    db = await get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        await websocket.close(code=1008, reason="User not found")
        return

    # Connect and register
    await manager.connect(websocket, conversation_id, str(user_id))
    logger.info(f"WebSocket connected: conversation={conversation_id}, user={user_id}")

    # Send connected event
    await websocket.send_json({
        "type": "connected",
        "conversation_id": conversation_id,
        "user_id": user_id,
    })

    # Listen for messages
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "send_message":
                try:
                    # Process message
                    content = data.get("content", "")
                    if not content:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Message content is required",
                        })
                        continue

                    # Create message via API (for persistence)
                    message = await StudyBuddyMessagingService.create_message(
                        conversation_id,
                        user_id,
                        content
                    )

                    # Get JSON-serializable dict from Pydantic model
                    message_dict = message.model_dump(mode='json')

                    # Send message sent confirmation
                    await websocket.send_json({
                        "type": "message_sent",
                        "conversation_id": conversation_id,
                        "message": message_dict,
                    })

                    # Broadcast to other participants
                    await manager.broadcast(
                        conversation_id,
                        {
                            "type": "new_message",
                            "conversation_id": conversation_id,
                            "message": message_dict,
                        },
                        exclude_socket=websocket
                    )

                except ValueError as e:
                    logger.error(f"Message validation error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                    })
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": "Failed to send message",
                    })


            elif message_type == "leave_conversation":
                await websocket.send_json({
                    "type": "disconnected",
                    "reason": "User left conversation",
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: conversation={conversation_id}, user={user_id}")
        manager.disconnect(websocket, conversation_id, user_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


# ============================================================================
# Peer Q&A Routes
# ============================================================================

@router.post("/qa/questions", response_model=dict)
async def create_question(
    data: QuestionCreate = Body(...),
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Create a new question.
    """
    try:
        question = await QaService.create_question(
            author_id=str(user.id),
            content=data.content,
            subject=data.subject,
            images=data.images or []
        )
        return {
            "success": True,
            "message": "Question created successfully",
            "data": question.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_008"}
        )
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create question", "error_code": "SBY_001"}
        )


@router.get("/qa/questions", response_model=dict)
async def get_questions(
    page: int = 1,
    per_page: int = 50,
    subject: Optional[str] = None,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get questions with pagination and optional subject filter.
    """
    try:
        result = await QaService.get_questions(page=page, per_page=per_page, subject=subject)
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} questions",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get questions", "error_code": "SBY_001"}
        )


@router.get("/qa/questions/{question_id}", response_model=dict)
async def get_question(
    question_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get a question by ID.
    """
    try:
        question = await QaService.get_question(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Question not found", "error_code": "SBY_009"}
            )
        return {
            "success": True,
            "message": "Question retrieved successfully",
            "data": question.model_dump(by_alias=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get question", "error_code": "SBY_001"}
        )


@router.put("/qa/questions/{question_id}", response_model=dict)
async def update_question(
    question_id: str,
    user: UserInDB = Depends(get_current_active_user),
    data: QuestionUpdate = None,
):
    """
    Update a question (only by author).
    """
    try:
        question = await QaService.update_question(question_id, str(user.id), data)
        return {
            "success": True,
            "message": "Question updated successfully",
            "data": question.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error updating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_010"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update question", "error_code": "SBY_001"}
        )


@router.delete("/qa/questions/{question_id}", response_model=dict)
async def delete_question(
    question_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Delete a question (only by author).
    """
    try:
        import traceback
        logger.error(f"DEBUG: delete_question called with question_id={question_id}")
        success = await QaService.delete_question(question_id, str(user.id))
        logger.error(f"DEBUG: QaService.delete_question returned {success}")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Question not found", "error_code": "SBY_009"}
            )
        return {
            "success": True,
            "message": "Question deleted successfully",
            "data": {},
        }
    except ValueError as e:
        logger.error(f"Error deleting question: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_010"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete question", "error_code": "SBY_001"}
        )


@router.post("/qa/answers", response_model=dict)
async def create_answer(
    data: AnswerCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Create an answer to a question.
    """
    try:
        answer = await QaService.create_answer(
            question_id=data.question_id,
            author_id=str(user.id),
            content=data.content,
            images=data.images or [],
            links=data.links or []
        )
        return {
            "success": True,
            "message": "Answer created successfully",
            "data": answer.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error creating answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_011"}
        )
    except Exception as e:
        logger.error(f"Error creating answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create answer", "error_code": "SBY_001"}
        )


@router.get("/qa/questions/{question_id}/answers", response_model=dict)
async def get_answers(
    question_id: str,
    page: int = 1,
    per_page: int = 50,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get answers for a question with pagination.
    """
    try:
        result = await QaService.get_answers(question_id, page=page, per_page=per_page)
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} answers",
            "data": result,
        }
    except ValueError as e:
        logger.error(f"Error getting answers: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e), "error_code": "SBY_012"}
        )
    except Exception as e:
        logger.error(f"Error getting answers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get answers", "error_code": "SBY_001"}
        )


@router.put("/qa/answers/{answer_id}", response_model=dict)
async def update_answer(
    answer_id: str,
    user: UserInDB = Depends(get_current_active_user),
    data: AnswerUpdate = None,
):
    """
    Update an answer (only by author).
    """
    try:
        answer = await QaService.update_answer(answer_id, str(user.id), data)
        return {
            "success": True,
            "message": "Answer updated successfully",
            "data": answer.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error updating answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_013"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update answer", "error_code": "SBY_001"}
        )


@router.delete("/qa/answers/{answer_id}", response_model=dict)
async def delete_answer(
    answer_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Delete an answer (only by author).
    """
    try:
        success = await QaService.delete_answer(answer_id, str(user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Answer not found", "error_code": "SBY_012"}
            )
        return {
            "success": True,
            "message": "Answer deleted successfully",
            "data": {},
        }
    except ValueError as e:
        logger.error(f"Error deleting answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_013"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete answer", "error_code": "SBY_001"}
        )


# ============================================================================
# Q&A Comment Routes
# ============================================================================

@router.post("/qa/comments", response_model=dict)
async def create_comment(
    data: CommentCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Create a new comment or reply for a question.
    """
    try:
        comment = await QaService.create_comment(str(user.id), data)
        return {
            "success": True,
            "message": "Comment created successfully",
            "data": comment.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_021"}
        )
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create comment", "error_code": "SBY_001"}
        )


@router.get("/qa/questions/{question_id}/comments", response_model=dict)
async def get_comments(
    question_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get all comments for a question.
    """
    try:
        comments = await QaService.get_comments(question_id)
        return {
            "success": True,
            "message": f"Found {len(comments)} comments",
            "data": [c.model_dump() for c in comments],
        }
    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get comments", "error_code": "SBY_001"}
        )


@router.put("/qa/comments/{comment_id}", response_model=dict)
async def update_comment(
    comment_id: str,
    data: CommentUpdate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Update a comment (only by author).
    """
    try:
        comment = await QaService.update_comment(comment_id, str(user.id), data.content)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Comment not found", "error_code": "SBY_022"}
            )
        return {
            "success": True,
            "message": "Comment updated successfully",
            "data": comment.model_dump(by_alias=True),
        }
    except ValueError as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_023"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update comment", "error_code": "SBY_001"}
        )


@router.delete("/qa/comments/{comment_id}", response_model=dict)
async def delete_comment(
    comment_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Delete a comment (only by author).
    """
    try:
        success = await QaService.delete_comment(comment_id, str(user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Comment not found", "error_code": "SBY_022"}
            )
        return {
            "success": True,
            "message": "Comment deleted successfully",
            "data": {},
        }
    except ValueError as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_023"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete comment", "error_code": "SBY_001"}
        )


# ============================================================================
# Study Room Routes
# ============================================================================

@router.post("/study-rooms", response_model=dict)
async def create_room(
    data: StudyRoomCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Create a new study room.
    """
    try:
        room = await StudyRoomService.create_room(
            host_id=str(user.id),
            major=data.major,
            subject=data.subject,
            title=data.title,
            description=data.description
        )
        return {
            "success": True,
            "message": "Study room created successfully",
            "data": room.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_014"}
        )
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create room", "error_code": "SBY_001"}
        )


@router.get("/study-rooms/active", response_model=dict)
async def get_active_rooms(
    page: int = 1,
    per_page: int = 50,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get all active study rooms.
    """
    try:
        result = await StudyRoomService.get_active_rooms(page=page, per_page=per_page)
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} active rooms",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error getting active rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get active rooms", "error_code": "SBY_001"}
        )


@router.post("/study-rooms/{room_id}/join", response_model=dict)
async def join_room(
    data: StudyRoomJoinRequest,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Join a study room with atomic capacity protection.
    """
    try:
        # Check if user is already participant
        if await StudyRoomService.is_user_participant(data.room_id, str(user.id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Already a participant in this room", "error_code": "SBY_015"}
            )

        participant = await StudyRoomService.join_room(data.room_id, str(user.id))

        return {
            "success": True,
            "message": "Successfully joined room",
            "data": participant.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Error joining room: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_016"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to join room", "error_code": "SBY_001"}
        )


@router.post("/study-rooms/{room_id}/leave", response_model=dict)
async def leave_room(
    room_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Leave a study room.
    """
    try:
        success = await StudyRoomService.leave_room(room_id, str(user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Room not found", "error_code": "SBY_017"}
            )
        return {
            "success": True,
            "message": "Successfully left room",
            "data": {},
        }
    except ValueError as e:
        logger.error(f"Error leaving room: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "SBY_018"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to leave room", "error_code": "SBY_001"}
        )


@router.post("/study-rooms/{room_id}/end", response_model=dict)
async def end_room(
    room_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    End a study room (only by host).
    """
    try:
        success = await StudyRoomService.end_room(room_id, str(user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Room not found", "error_code": "SBY_017"}
            )
        return {
            "success": True,
            "message": "Room ended successfully",
            "data": {},
        }
    except ValueError as e:
        logger.error(f"Error ending room: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_019"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to end room", "error_code": "SBY_001"}
        )


@router.put("/study-rooms/{room_id}", response_model=dict)
async def update_room(
    room_id: str,
    user: UserInDB = Depends(get_current_active_user),
    data: StudyRoomUpdate = None,
):
    """
    Update room details (only by host).
    """
    try:
        room = await StudyRoomService.update_room(room_id, str(user.id), data)
        return {
            "success": True,
            "message": "Room updated successfully",
            "data": room.model_dump(),
        }
    except ValueError as e:
        logger.error(f"Error updating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "SBY_020"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update room", "error_code": "SBY_001"}
        )


@router.get("/study-rooms/{room_id}", response_model=dict)
async def get_room(
    room_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get a study room by ID.
    """
    try:
        room = await StudyRoomService.get_room(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Room not found", "error_code": "SBY_017"}
            )
        return {
            "success": True,
            "message": "Room retrieved successfully",
            "data": room.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get room", "error_code": "SBY_001"}
        )


# ============================================================================
# Study Room WebSocket Real-Time Messaging
# ============================================================================


class RoomConnectionManager:
    """Manage WebSocket connections for study room messaging."""

    def __init__(self):
        # Dictionary: room_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Dictionary: room_id -> set of user IDs
        self.room_participants: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            self.room_participants[room_id] = set()
        self.active_connections[room_id].append(websocket)
        self.room_participants[room_id].add(user_id)

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Remove a WebSocket connection."""
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            self.room_participants[room_id].discard(user_id)
            if not self.room_participants[room_id]:
                del self.room_participants[room_id]

    async def broadcast(
        self,
        room_id: str,
        message: dict,
        exclude_socket: Optional[WebSocket] = None
    ):
        """Broadcast a message to all participants in a room."""
        if room_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[room_id]:
            try:
                if exclude_socket and connection == exclude_socket:
                    continue
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection, room_id, "")
            try:
                await connection.close()
            except Exception:
                pass



# Global room connection manager
room_manager = RoomConnectionManager()


@router.get("/study-rooms/{room_id}/messages", response_model=dict)
async def get_room_messages(
    room_id: str,
    page: int = 1,
    per_page: int = 50,
    user: UserInDB = Depends(get_current_active_user),
):
    """
    Get messages for a study room with pagination.
    """
    try:
        result = await StudyRoomMessagingService.get_room_messages(room_id, page=page, per_page=per_page)
        
        # Convert Pydantic models in the result to dicts for JSON serialization
        messages_dict = [m.model_dump(mode='json') for m in result["messages"]]
        
        return {
            "success": True,
            "message": f"Found {result['meta']['total']} messages",
            "data": {
                "messages": messages_dict,
                "meta": result["meta"]
            },
        }
    except ValueError as e:
        logger.error(f"Error getting room messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e), "error_code": "SBY_021"}
        )
    except Exception as e:
        logger.error(f"Error getting room messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get room messages", "error_code": "SBY_001"}
        )


@router.websocket("/ws/rooms/{room_id}")
async def study_room_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(..., description="JWT Access Token")
):
    """
    WebSocket endpoint for real-time study room messaging.

    Connect with:
    - Authorization: JWT Bearer token (passed as query parameter for compatibility)
    - Query params: room_id, token

    This WebSocket requires users to be active room participants.
    """
    # Extract user_id from JWT token
    try:
        user_id = get_current_user_id(token)
    except Exception as e:
        logger.warning(f"Study Room WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    # Verify user exists
    db = await get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        await websocket.close(code=1008, reason="User not found")
        return

    # Connect and register
    await room_manager.connect(websocket, room_id, str(user_id))

    logger.info(f"Study Room WebSocket connected: room={room_id}, user={user_id}")

    # Send connected event
    await websocket.send_json({
        "type": "connected",
        "room_id": room_id,
        "user_id": user_id,
    })

    # Listen for messages
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "send_message":
                try:
                    # Process message
                    content = data.get("content", "")
                    if not content:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Message content is required",
                        })
                        continue

                    # Create message via API (for persistence)
                    message = await StudyRoomMessagingService.create_message(
                        room_id,
                        user_id,
                        content
                    )

                    # Send message sent confirmation
                    await websocket.send_json({
                        "type": "message_sent",
                        "room_id": room_id,
                        "message": message.model_dump(mode='json'),
                    })

                    # Broadcast to other participants
                    await room_manager.broadcast(
                        room_id,
                        {
                            "type": "new_message",
                            "room_id": room_id,
                            "message": message.model_dump(mode='json'),
                        },
                        exclude_socket=websocket
                    )


                except ValueError as e:
                    logger.error(f"Message validation error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                    })
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": "Failed to send message",
                    })

            elif message_type == "leave_room":
                await websocket.send_json({
                    "type": "disconnected",
                    "reason": "User left room",
                })
                break

    except WebSocketDisconnect:
        logger.info(f"Study Room WebSocket disconnected: room={room_id}, user={user_id}")
        room_manager.disconnect(websocket, room_id, user_id)

    except Exception as e:
        logger.error(f"Study Room WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))
