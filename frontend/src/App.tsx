import React from 'react';
import { useState, type FormEvent } from 'react';
import { postChatQuestion, type ChatResponse } from './api/chat';
import AcademicAnswer from './components/AcademicAnswer';
import DeadlineAnswer from './components/DeadlineAnswer';
import PolicyAnswer from './components/PolicyAnswer';

const POLICY_TERMS = [
  'policy',
  'procedure',
  'parking',
  'citation',
  'ticket',
  'grade appeal',
  'appeal process',
  'academic standing',
  'registration process',
  'register for',
];

function isPolicyQuestion(question: string): boolean {
  const normalized = question.toLowerCase();
  return POLICY_TERMS.some((term) => normalized.includes(term));
}

function isDeadlineQuestion(question: string): boolean {
  return /\b(add\/drop|add|drop|withdraw|deadline)\b/i.test(question);
}

function isAcademicQuestion(question: string): boolean {
  const normalized = question.toLowerCase();
  return [
    'academic',
    'catalog',
    'college',
    'course',
    'degree',
    'graduat',
    'major',
    'plan of study',
    'prerequisite',
    'program',
    'requirement',
  ].some((term) => normalized.includes(term));
}

export default function App() {
  const [question, setQuestion] = useState('');
  const [term, setTerm] = useState('');
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [answerKind, setAnswerKind] = useState<
    'deadline' | 'policy' | 'academic' | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setAnswerKind(
      isPolicyQuestion(trimmedQuestion)
        ? 'policy'
        : isDeadlineQuestion(trimmedQuestion)
          ? 'deadline'
          : isAcademicQuestion(trimmedQuestion)
            ? 'academic'
            : 'deadline',
    );

    try {
      const publicContext = term.trim() ? { term: term.trim() } : undefined;
      const result = await postChatQuestion(trimmedQuestion, publicContext);
      setResponse(result);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'The request could not be completed. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>PNW Information Chatbot</h1>
      <p>Ask about general PNW policies, procedures, or deadlines. Do not include personal or student-specific information.</p>
      <form onSubmit={submitQuestion}>
        <label htmlFor="question">Question</label>
        <textarea
          id="question"
          name="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          required
          maxLength={2000}
          rows={3}
        />
        <label htmlFor="term">Academic term (if known)</label>
        <input
          id="term"
          name="term"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
          autoComplete="off"
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Checking…' : 'Ask'}
        </button>
      </form>
      {error ? <p role="alert">{error}</p> : null}
      {response !== null && answerKind === 'policy' ? (
        <PolicyAnswer response={response} />
      ) : null}
      {response !== null && answerKind === 'academic' ? (
        <AcademicAnswer response={response} />
      ) : null}
      {response !== null && (answerKind === 'deadline' || answerKind === null) ? (
        <DeadlineAnswer response={response} />
      ) : null}
    </main>
  );
}
