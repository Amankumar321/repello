const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export interface Message {
  type: 'status' | 'content' | 'error';
  content: string;
}

interface QueryRequest {
  query: string;
  sessionId: string | null;
  max_results?: number | null;
}

// In-memory session storage
let currentSessionId: string | null = null;

export async function* streamQuery(query: string): AsyncGenerator<Message> {
  try {
    const headers = {
      'Content-Type': 'application/json',
    };

    const requestBody: QueryRequest = {
      query: query.trim(),
      sessionId: currentSessionId,
      max_results: null
    };

    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      if (response.status === 429) {
        yield {
          type: 'error',
          content: 'Too many requests. Please wait a minute before trying again.'
        };
        return;
      }
      throw new Error('Network response was not ok');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is null');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        if (buffer) {
          try {
            const message = JSON.parse(buffer) as Message;
            if ('sessionId' in message) {
              currentSessionId = (message as any).sessionId;
              continue;
            }
            yield message;
          } catch (e) {
            // Silently handle parse errors for final buffer
          }
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim()) {
          try {
            const message = JSON.parse(line);
            if ('sessionId' in message) {
              currentSessionId = message.sessionId;
              continue;
            }
            yield message as Message;
          } catch (e) {
            // Silently handle parse errors
          }
        }
      }
    }
  } catch (error) {
    yield {
      type: 'error',
      content: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
} 