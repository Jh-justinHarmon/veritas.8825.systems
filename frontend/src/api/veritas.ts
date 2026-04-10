/**
 * Veritas API Client
 * 
 * Connects frontend to Flask backend for concept-driven answer synthesis.
 */

export interface VeritasIdea {
  title: string;
  paragraphs: string[];
  sourceIds: string[];
}

export interface VeritasAnswer {
  question: string;
  ideas: VeritasIdea[];
  sources: Record<string, string>;
}

export interface ExampleQuestion {
  id: string;
  question: string;
  description: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  question: string;
  preview: string;
  idea_count: number;
  source_count: number;
}

export interface HistoryDetail {
  id: string;
  timestamp: string;
  question: string;
  answer: {
    ideas: VeritasIdea[];
    sources: Record<string, any>;
  };
  trace: {
    retrieved_chunks: Array<{
      source_name: string;
      title: string;
      tier: number;
      text_preview: string;
    }>;
    chunk_count: number;
    synthesis_model: string;
    timestamp: string;
  };
}

const API_BASE_URL = 'http://localhost:5001';

/**
 * Synthesize concept-driven answer from question.
 * 
 * @param question - User's question (5-500 chars)
 * @returns Promise<VeritasAnswer>
 * @throws Error if synthesis fails
 */
export async function synthesizeAnswer(question: string): Promise<VeritasAnswer> {
  const response = await fetch(`${API_BASE_URL}/api/synthesize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Synthesis failed' }));
    throw new Error(error.message || 'Failed to synthesize answer');
  }

  return await response.json();
}

/**
 * Get example questions for testing.
 * 
 * @returns Promise<ExampleQuestion[]>
 */
export async function getExamples(): Promise<ExampleQuestion[]> {
  const response = await fetch(`${API_BASE_URL}/api/examples`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch examples');
  }
  
  return await response.json();
}

/**
 * Check API health status.
 * 
 * @returns Promise<{ status: string, chunks_loaded: number }>
 */
export async function checkHealth(): Promise<{ status: string; chunks_loaded: number; service: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  
  return response.json();
}

/**
 * Get history entries.
 * 
 * @param limit - Maximum number of entries to return (default: 50)
 * @param offset - Offset for pagination (default: 0)
 * @returns Promise<HistoryEntry[]>
 */
export async function getHistory(limit: number = 50, offset: number = 0): Promise<HistoryEntry[]> {
  const response = await fetch(`${API_BASE_URL}/history?limit=${limit}&offset=${offset}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }
  
  return response.json();
}

/**
 * Get history entry by ID.
 * 
 * @param sessionId - ID of the history entry
 * @returns Promise<HistoryDetail>
 */
export async function getHistoryById(sessionId: string): Promise<HistoryDetail> {
  const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch history entry ${sessionId}`);
  }
  
  return response.json();
}

/**
 * Delete history entry by ID.
 * 
 * @param sessionId - ID of the history entry
 * @returns Promise<void>
 */
export async function deleteHistory(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/history/${sessionId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete history entry ${sessionId}`);
  }
}
