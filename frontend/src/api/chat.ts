export type ChatOutcome = 'answered' | 'needs_context' | 'cannot_verify' | 'escalation_required';

export interface ChatContext {
  campus?: 'Hammond' | 'Westville';
  term?: string;
  program?: string;
  courseCode?: string;
  academicLevel?: 'undergraduate' | 'graduate';
}

export interface Citation {
  title: string;
  url: string;
  locator: string;
}

export interface Escalation {
  office: string;
  reason: string;
  contactUrl?: string;
}

export interface ChatResponse {
  outcome: ChatOutcome;
  message: string;
  requiredContext?: Array<'campus' | 'term' | 'program' | 'courseCode' | 'academicLevel'>;
  citations: Citation[];
  escalation?: Escalation;
}

export async function postChatQuestion(question: string, context?: ChatContext): Promise<ChatResponse> {
  const response = await fetch('/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message ?? 'Request failed');
  }

  return response.json();
}
