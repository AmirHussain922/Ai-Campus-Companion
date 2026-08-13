import { useStore } from '../store';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002') + '/api';

export interface Question {
  _id: string;
  author_id: string;
  author_full_name: string;
  content: string;
  subject: string;
  images: string[];
  answers_count: number;
  created_at: string;
  updated_at: string;
}

export interface Answer {
  _id: string;
  question_id: string;
  author_id: string;
  author_full_name: string;
  content: string;
  images: string[];
  links: string[];
  created_at: string;
}

export interface QuestionCreateData {
  content: string;
  subject: string;
  images?: string[];
}

export interface QuestionUpdateData {
  content?: string;
  subject?: string;
  images?: string[];
}

export interface AnswerCreateData {
  question_id: string;
  content: string;
  images?: string[];
  links?: string[];
}

export interface AnswerUpdateData {
  content?: string;
  images?: string[];
  links?: string[];
}

export interface Comment {
  _id: string;
  question_id: string;
  author_id: string;
  author_full_name: string;
  content: string;
  parent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CommentCreateData {
  question_id: string;
  content: string;
  parent_id?: string;
}

class QaService {
  private getHeaders() {
    const token = useStore.getState().authToken;
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  async listQuestions(page: number = 1, limit: number = 20, subject?: string): Promise<{ questions: Question[], total: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (subject) params.append('subject', subject);

    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions?${params.toString()}`, {
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to fetch questions');
    }

    const data = await resp.json();
    return {
      questions: data.data.questions,
      total: data.data.meta.total,
    };
  }

  async getQuestion(questionId: string): Promise<Question> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions/${questionId}`, {
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to fetch question');
    }

    const data = await resp.json();
    return data.data;
  }

  async createQuestion(data: QuestionCreateData): Promise<Question> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to create question');
    }

    const result = await resp.json();
    return result.data;
  }

  async updateQuestion(questionId: string, data: QuestionUpdateData): Promise<Question> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions/${questionId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to update question');
    }

    const result = await resp.json();
    return result.data;
  }

  async deleteQuestion(questionId: string): Promise<void> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions/${questionId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to delete question');
    }
  }

  async listAnswers(questionId: string): Promise<Answer[]> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions/${questionId}/answers`, {
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to fetch answers');
    }

    const data = await resp.json();
    return data.data.answers;
  }

  async createAnswer(data: AnswerCreateData): Promise<Answer> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/answers`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to create answer');
    }

    const result = await resp.json();
    return result.data;
  }

  async updateAnswer(answerId: string, data: AnswerUpdateData): Promise<Answer> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/answers/${answerId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to update answer');
    }

    const result = await resp.json();
    return result.data;
  }

  async deleteAnswer(answerId: string): Promise<void> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/answers/${answerId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to delete answer');
    }
  }

  async uploadImage(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    const token = useStore.getState().authToken;
    const resp = await fetch(`${API_BASE_URL}/media/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to upload image');
    }

    const data = await resp.json();
    return data.url;
  }

  async listComments(questionId: string): Promise<Comment[]> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/questions/${questionId}/comments`, {
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to fetch comments');
    }

    const data = await resp.json();
    return data.data;
  }

  async createComment(data: CommentCreateData): Promise<Comment> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/comments`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to create comment');
    }

    const result = await resp.json();
    return result.data;
  }

  async updateComment(commentId: string, content: string): Promise<Comment> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/comments/${commentId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify({ content }),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to update comment');
    }

    const result = await resp.json();
    return result.data;
  }

  async deleteComment(commentId: string): Promise<void> {
    const resp = await fetch(`${API_BASE_URL}/study-buddy/qa/comments/${commentId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail?.message || 'Failed to delete comment');
    }
  }
}

export const qaService = new QaService();
