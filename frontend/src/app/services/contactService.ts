import axios from 'axios';

// API base URL - follows project convention
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

export interface ContactFormData {
  name?: string;
  email?: string;
  feedback_type: 'general' | 'bug' | 'feature' | 'suggestion' | 'other';
  message: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
  data?: {
    submission_id?: string;
  };
  error_code?: string;
}

export interface ContactFormState {
  status: 'idle' | 'loading' | 'success' | 'error';
  error?: string;
}

/**
 * Submit a contact form submission
 */
export async function submitContactForm(
  data: ContactFormData
): Promise<ApiResponse> {
  const response = await axios.post<ApiResponse>(
    `${API_BASE_URL}/contact`,
    data,
    {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    }
  );
  return response.data;
}

/**
 * Get rate limit status for contact form
 */
export async function checkContactRateLimit(): Promise<{
  allowed: boolean;
  limit: number;
  remaining: number;
  reset_at: number;
}> {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/contact/health`,
      {
        timeout: 5000,
      }
    );
    return response.data;
  } catch (error: any) {
    // If rate limit check fails, allow the request
    // Backend will handle the rate limiting
    return {
      allowed: true,
      limit: 100,
      remaining: 100,
      reset_at: 0,
    };
  }
}
