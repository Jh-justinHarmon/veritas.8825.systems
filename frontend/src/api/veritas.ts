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

// Use relative path in production, localhost in development
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Synthesize concept-driven answer from question.
 * 
 * @param question - User's question (5-500 chars)
 * @param mode - Synthesis mode (raw or abstracted)
 * @returns Promise<any>
 * @throws Error if synthesis fails
 */
export async function synthesizeAnswer(question: string, mode: 'raw' | 'abstracted' = 'raw'): Promise<any> {
  const endpoint = mode === 'abstracted' ? `${API_BASE_URL}/api/synthesize/abstracted` : `${API_BASE_URL}/api/synthesize`;
  
  console.log(`[API] Fetching ${endpoint}`);
  
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    
    console.log(`[API] Response status: ${response.status}`);
    
    if (!response.ok) {
      throw new Error(`Synthesis failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] Response data:`, data);
    return data;
  } catch (error) {
    console.error(`[API] Fetch error:`, error);
    throw error;
  }
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
  const response = await fetch(`${API_BASE_URL}/api/health`);
  
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
  const response = await fetch(`${API_BASE_URL}/api/history?limit=${limit}&offset=${offset}`);
  
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
  const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}`);
  
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
  const response = await fetch(`${API_BASE_URL}/api/history/${sessionId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete history entry ${sessionId}`);
  }
}
