"""
Peer Q&A Service for AI Campus Companion.

Handles academic questions, answers, and discussions.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from bson.errors import InvalidId
from app.models import (
    QuestionInDB,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    AnswerInDB,
    AnswerCreate,
    AnswerResponse,
    AnswerUpdate,
    CommentInDB,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.core.database import (
    get_database,
    get_qa_questions_collection,
    get_qa_answers_collection,
    get_qa_comments_collection,
    get_users_collection
)
import logging

logger = logging.getLogger(__name__)


class QaService:
    """Service for managing Q&A system."""

    @staticmethod
    async def create_question(
        author_id: str,
        content: str,
        subject: str,
        images: List[str] = None
    ) -> QuestionResponse:
        """
        Create a new question.

        Args:
            author_id: Author user ID
            content: Question content
            subject: Subject/category
            images: List of image URLs

        Returns:
            QuestionResponse
        """
        questions_col = await get_qa_questions_collection()

        # Validate content
        content_stripped = content.strip()
        if not content_stripped:
            raise ValueError("Question content is required")
        if len(content_stripped) > 5000:
            content_stripped = content_stripped[:5000]

        # Validate subject
        subject_stripped = subject.strip().lower()
        if not subject_stripped:
            raise ValueError("Subject is required")

        # Create question
        question = QuestionInDB(
            author_id=author_id,
            content=content_stripped,
            subject=subject_stripped,
            images=images or [],
        )
        result = await questions_col.insert_one(question.model_dump(exclude={"id"}))
        question.id = ObjectId(result.inserted_id)

        # Get author info
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(author_id)})

        return QuestionResponse(
            id=str(question.id),
            author_id=question.author_id,
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=question.content,
            subject=question.subject,
            images=question.images,
            answers_count=0,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )

    @staticmethod
    async def get_question(question_id: str) -> Optional[QuestionResponse]:
        """
        Get a question by ID.

        Args:
            question_id: Question ID

        Returns:
            QuestionResponse or None
        """
        try:
            oid = ObjectId(question_id)
        except InvalidId:
            return None

        questions_col = await get_qa_questions_collection()

        question = await questions_col.find_one({"_id": oid})
        if not question:
            return None

        # Get author info with ObjectId validation
        users_col = await get_users_collection()
        try:
            author = await users_col.find_one({"_id": ObjectId(question["author_id"])})
        except (InvalidId, ValueError):
            author = None

        return QuestionResponse(
            id=str(question["_id"]),
            author_id=question["author_id"],
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=question["content"],
            subject=question["subject"],
            images=question["images"],
            answers_count=question.get("answers_count", 0),
            created_at=question["created_at"],
            updated_at=question["updated_at"],
        )

    @staticmethod
    async def get_questions(
        page: int = 1,
        per_page: int = 50,
        subject: Optional[str] = None
    ) -> dict:
        """
        Get questions with pagination and optional subject filter.

        Args:
            page: Page number
            per_page: Items per page
            subject: Optional subject filter

        Returns:
            Dictionary with questions and pagination meta
        """
        questions_col = await get_qa_questions_collection()
        users_col = await get_users_collection()

        # Build query with consistent subject normalization
        query = {}
        if subject:
            query["subject"] = subject.lower().strip()

        # Get total count
        total = await questions_col.count_documents(query)

        # Validate and clamp pagination values
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 50

        # Get questions with pagination
        skip = (page - 1) * per_page
        cursor = questions_col.find(query).sort("created_at", -1).skip(skip).limit(per_page)

        questions = []
        async for doc in cursor:
            try:
                author = await users_col.find_one({"_id": ObjectId(doc["author_id"])})
                author_full_name = author.get("full_name", "Anonymous") if author else "Anonymous"
            except (InvalidId, ValueError):
                author = None
                author_full_name = "Anonymous"
            questions.append({
                "_id": str(doc["_id"]),
                "author_id": doc["author_id"],
                "author_full_name": author_full_name,
                "content": doc["content"],
                "subject": doc["subject"],
                "images": doc.get("images", []),
                "answers_count": doc.get("answers_count", 0),
                "created_at": doc["created_at"],
                "updated_at": doc["updated_at"],
            })

        total_pages = (total + per_page - 1) // per_page

        return {
            "questions": questions,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    @staticmethod
    async def update_question(
        question_id: str,
        author_id: str,
        update_data: QuestionUpdate
    ) -> Optional[QuestionResponse]:
        """
        Update a question (only by author).

        Args:
            question_id: Question ID
            author_id: Author user ID (must be question author)
            update_data: Update data

        Returns:
            Updated QuestionResponse or None
        """
        try:
            oid = ObjectId(question_id)
        except InvalidId:
            return None

        questions_col = await get_qa_questions_collection()

        # Get question to verify ownership
        question = await questions_col.find_one({"_id": oid})
        if not question:
            return None

        # Verify ownership
        if question["author_id"] != author_id:
            raise ValueError("Only question author can update question")

        # Build update document
        update_data_dict = update_data.model_dump(exclude_unset=True)

        # Validate and limit content length if provided
        if "content" in update_data_dict:
            content = update_data_dict["content"].strip()
            if not content:
                raise ValueError("Question content cannot be empty")
            if len(content) > 5000:
                content = content[:5000]
            update_data_dict["content"] = content
        
        if "subject" in update_data_dict:
            subject = update_data_dict["subject"].strip().lower()
            if not subject:
                raise ValueError("Subject cannot be empty")
            update_data_dict["subject"] = subject

        if update_data_dict:
            update_data_dict["updated_at"] = datetime.utcnow()
            await questions_col.update_one(
                {"_id": ObjectId(question_id)},
                {"$set": update_data_dict}
            )

            # Get updated question
            question = await questions_col.find_one({"_id": ObjectId(question_id)})

        # Get author info
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(question["author_id"])})

        return QuestionResponse(
            id=str(question["_id"]),
            author_id=question["author_id"],
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=question["content"],
            subject=question["subject"],
            images=question.get("images", []),
            answers_count=question.get("answers_count", 0),
            created_at=question["created_at"],
            updated_at=question["updated_at"],
        )

    @staticmethod
    async def delete_question(question_id: str, author_id: str) -> bool:
        """
        Delete a question (only by author).

        Args:
            question_id: Question ID
            author_id: Author user ID (must be question author)

        Returns:
            True if deleted, False if not found
        """
        print(f"DEBUG delete_question called with question_id={question_id}, author_id={author_id}", flush=True)
        try:
            oid = ObjectId(question_id)
        except InvalidId:
            print(f"DEBUG: Invalid ObjectId", flush=True)
            return False

        questions_col = await get_qa_questions_collection()
        answers_col = await get_qa_answers_collection()
        comments_col = await get_qa_comments_collection()
        print(f"DEBUG: Got collections, answers_col={answers_col}, comments_col={comments_col}", flush=True)

        # Get question to verify ownership
        question = await questions_col.find_one({"_id": oid})
        if not question:
            print(f"DEBUG: Question not found", flush=True)
            return False

        print(f"DEBUG: Question found: {question.get('content')}", flush=True)

        # Verify ownership
        if question["author_id"] != author_id:
            print(f"DEBUG: Unauthorized - question author_id={question['author_id']}, requested_by={author_id}", flush=True)
            raise ValueError("Only question author can delete question")

        # Cascade delete: delete all answers and comments first
        question_oid = ObjectId(question_id)
        print(f"DEBUG: Deleting answers for question {question_id}", flush=True)
        result_answers = await answers_col.delete_many({"question_id": question_id})
        print(f"DEBUG: Deleted {result_answers.deleted_count} answers", flush=True)

        print(f"DEBUG: Deleting comments for question {question_id}", flush=True)
        result_comments = await comments_col.delete_many({"question_id": question_id})
        print(f"DEBUG: Deleted {result_comments.deleted_count} comments", flush=True)

        # Delete question
        result = await questions_col.delete_one({"_id": question_oid})
        print(f"DEBUG: Question deletion result: {result.deleted_count}", flush=True)
        return result.deleted_count > 0

    @staticmethod
    async def create_answer(
        question_id: str,
        author_id: str,
        content: str,
        images: List[str] = None,
        links: List[str] = None
    ) -> AnswerResponse:
        """
        Create an answer to a question.

        Args:
            question_id: Question ID
            author_id: Answer author ID
            content: Answer content
            images: List of image URLs
            links: List of links

        Returns:
            AnswerResponse
        """
        try:
            q_oid = ObjectId(question_id)
        except InvalidId:
            raise ValueError("Invalid question ID")

        db = await get_database()
        questions_col = await get_qa_questions_collection()
        answers_col = await get_qa_answers_collection()

        # Validate content
        if not content or len(content.strip()) == 0:
            raise ValueError("Answer content is required")

        # Get question
        question = await questions_col.find_one({"_id": q_oid})
        if not question:
            raise ValueError("Question not found")

        # Limit content length
        content = content.strip()
        if len(content) > 5000:
            content = content[:5000]

        # Create answer
        answer = AnswerInDB(
            question_id=question_id,
            author_id=author_id,
            content=content,
            images=images or [],
            links=links or [],
        )
        result = await answers_col.insert_one(answer.model_dump(exclude={"id"}))
        answer.id = ObjectId(result.inserted_id)

        # Update question answers count
        await questions_col.update_one(
            {"_id": ObjectId(question_id)},
            {"$inc": {"answers_count": 1}}
        )

        # Get author info
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(author_id)})

        return AnswerResponse(
            id=str(answer.id),
            question_id=answer.question_id,
            author_id=answer.author_id,
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=answer.content,
            images=answer.images,
            links=answer.links,
            created_at=answer.created_at,
        )

    @staticmethod
    async def get_answers(
        question_id: str,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """
        Get answers for a question with pagination.

        Args:
            question_id: Question ID
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with answers and pagination meta
        """
        answers_col = await get_qa_answers_collection()
        users_col = await get_users_collection()

        # Get total count
        total = await answers_col.count_documents({"question_id": question_id})

        # Validate and clamp pagination values
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 50

        # Get answers with pagination
        skip = (page - 1) * per_page
        cursor = answers_col.find({"question_id": question_id}).sort("created_at", 1).skip(skip).limit(per_page)

        answers = []
        async for doc in cursor:
            try:
                author = await users_col.find_one({"_id": ObjectId(doc["author_id"])})
                author_full_name = author.get("full_name", "Anonymous") if author else "Anonymous"
            except (InvalidId, ValueError):
                author = None
                author_full_name = "Anonymous"
            answers.append({
                "_id": str(doc["_id"]),
                "question_id": doc["question_id"],
                "author_id": doc["author_id"],
                "author_full_name": author_full_name,
                "content": doc["content"],
                "images": doc.get("images", []),
                "links": doc.get("links", []),
                "created_at": doc["created_at"],
            })

        total_pages = (total + per_page - 1) // per_page

        return {
            "answers": answers,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    @staticmethod
    async def update_answer(
        answer_id: str,
        author_id: str,
        update_data: AnswerUpdate
    ) -> Optional[AnswerResponse]:
        """
        Update an answer (only by author).

        Args:
            answer_id: Answer ID
            author_id: Author user ID (must be answer author)
            update_data: Update data

        Returns:
            Updated AnswerResponse or None
        """
        try:
            oid = ObjectId(answer_id)
        except InvalidId:
            return None

        answers_col = await get_qa_answers_collection()

        # Get answer to verify ownership
        answer = await answers_col.find_one({"_id": oid})
        if not answer:
            return None

        # Verify ownership
        if answer["author_id"] != author_id:
            raise ValueError("Only answer author can update answer")

        # Build update document
        update_data_dict = update_data.model_dump(exclude_unset=True)

        # Validate and limit content length if provided
        if "content" in update_data_dict:
            content = update_data_dict["content"].strip()
            if not content:
                raise ValueError("Answer content cannot be empty")
            if len(content) > 5000:
                content = content[:5000]
            update_data_dict["content"] = content

        if update_data_dict:
            update_data_dict["updated_at"] = datetime.utcnow()
            await answers_col.update_one(
                {"_id": ObjectId(answer_id)},
                {"$set": update_data_dict}
            )

            # Get updated answer
            answer = await answers_col.find_one({"_id": ObjectId(answer_id)})

        # Get author info
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(answer["author_id"])})

        return AnswerResponse(
            id=str(answer["_id"]),
            question_id=answer["question_id"],
            author_id=answer["author_id"],
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=answer["content"],
            images=answer.get("images", []),
            links=answer.get("links", []),
            created_at=answer["created_at"],
        )

    @staticmethod
    async def delete_answer(answer_id: str, author_id: str) -> bool:
        """
        Delete an answer (only by author).

        Args:
            answer_id: Answer ID
            author_id: Author user ID (must be answer author)

        Returns:
            True if deleted, False if not found
        """
        try:
            oid = ObjectId(answer_id)
        except InvalidId:
            return False

        questions_col = await get_qa_questions_collection()
        answers_col = await get_qa_answers_collection()

        # Get answer to verify ownership
        answer = await answers_col.find_one({"_id": oid})
        if not answer:
            return False

        # Verify ownership
        if answer["author_id"] != author_id:
            raise ValueError("Only answer author can delete answer")

        # Get question ID to decrement counter
        question_id = answer["question_id"]

        # Delete answer
        result = await answers_col.delete_one({"_id": ObjectId(answer_id)})

        # Decrement answers_count in parent question
        if result.deleted_count > 0:
            await questions_col.update_one(
                {"_id": ObjectId(question_id)},
                {"$inc": {"answers_count": -1}}
            )

        return result.deleted_count > 0

    @staticmethod
    async def create_comment(
        author_id: str,
        data: CommentCreate
    ) -> CommentResponse:
        """
        Create a new comment or reply.
        """
        try:
            q_oid = ObjectId(data.question_id)
        except InvalidId:
            raise ValueError("Invalid question ID")

        if data.parent_id:
            try:
                ObjectId(data.parent_id)
            except InvalidId:
                raise ValueError("Invalid parent comment ID")

        questions_col = await get_qa_questions_collection()
        comments_col = await get_qa_comments_collection()

        # Validate question exists
        question = await questions_col.find_one({"_id": q_oid})
        if not question:
            raise ValueError("Question not found")

        # If it's a reply, validate parent exists and belongs to same question
        if data.parent_id:
            try:
                parent = await comments_col.find_one({"_id": ObjectId(data.parent_id)})
                if not parent:
                    raise ValueError("Parent comment not found")
                # Validate parent belongs to the same question
                if parent["question_id"] != data.question_id:
                    raise ValueError("Parent comment must belong to the same question")
            except InvalidId:
                raise ValueError("Invalid parent comment ID")

        # Validate content
        content_stripped = data.content.strip()
        if not content_stripped:
            raise ValueError("Comment content cannot be empty")

        # Create comment
        comment = CommentInDB(
            question_id=data.question_id,
            author_id=author_id,
            content=content_stripped,
            parent_id=data.parent_id
        )
        
        result = await comments_col.insert_one(comment.model_dump(exclude={"id"}))
        comment.id = ObjectId(result.inserted_id)

        # Get author info
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(author_id)})

        return CommentResponse(
            id=str(comment.id),
            question_id=comment.question_id,
            author_id=comment.author_id,
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=comment.content,
            parent_id=comment.parent_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )

    @staticmethod
    async def get_comments(question_id: str) -> List[CommentResponse]:
        """
        Get all comments for a question.
        """
        try:
            ObjectId(question_id)
        except InvalidId:
            return []

        comments_col = await get_qa_comments_collection()
        users_col = await get_users_collection()

        cursor = comments_col.find({"question_id": question_id}).sort("created_at", 1)
        
        comments = []
        async for doc in cursor:
            try:
                author = await users_col.find_one({"_id": ObjectId(doc["author_id"])})
                author_full_name = author.get("full_name", "Anonymous") if author else "Anonymous"
            except (InvalidId, ValueError):
                author = None
                author_full_name = "Anonymous"
            comments.append(CommentResponse(
                id=str(doc["_id"]),
                question_id=doc["question_id"],
                author_id=doc["author_id"],
                author_full_name=author_full_name,
                content=doc["content"],
                parent_id=doc.get("parent_id"),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"]
            ))
        
        return comments

    @staticmethod
    async def update_comment(
        comment_id: str,
        author_id: str,
        content: str
    ) -> Optional[CommentResponse]:
        """
        Update a comment (only by author).
        """
        try:
            oid = ObjectId(comment_id)
        except InvalidId:
            return None

        comments_col = await get_qa_comments_collection()

        comment = await comments_col.find_one({"_id": oid})
        if not comment:
            return None

        if comment["author_id"] != author_id:
            raise ValueError("Only comment author can update comment")

        # Validate content
        content_stripped = content.strip()
        if not content_stripped:
            raise ValueError("Comment content cannot be empty")

        await comments_col.update_one(
            {"_id": oid},
            {"$set": {"content": content_stripped, "updated_at": datetime.utcnow()}}
        )

        # Get updated comment
        doc = await comments_col.find_one({"_id": oid})
        users_col = await get_users_collection()
        author = await users_col.find_one({"_id": ObjectId(doc["author_id"])})

        return CommentResponse(
            id=str(doc["_id"]),
            question_id=doc["question_id"],
            author_id=doc["author_id"],
            author_full_name=author.get("full_name", "Anonymous") if author else "Anonymous",
            content=doc["content"],
            parent_id=doc.get("parent_id"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )

    @staticmethod
    async def delete_comment(comment_id: str, author_id: str) -> bool:
        """
        Delete a comment (only by author).
        """
        try:
            oid = ObjectId(comment_id)
        except InvalidId:
            return False

        comments_col = await get_qa_comments_collection()

        comment = await comments_col.find_one({"_id": oid})
        if not comment:
            return False

        if comment["author_id"] != author_id:
            raise ValueError("Only comment author can delete comment")

        # Also delete sub-replies
        await comments_col.delete_many({"parent_id": comment_id})
        result = await comments_col.delete_one({"_id": oid})
        
        return result.deleted_count > 0
