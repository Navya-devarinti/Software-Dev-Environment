import React from 'react';

type DeadlineAnswerProps = {
  response?: unknown;
};

type Citation = {
  title?: string;
  url?: string;
  locator?: string;
};

type Escalation = {
  office?: string;
  contactUrl?: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function nonemptyString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value.trim() : undefined;
}

function isHttpUrl(value: string | undefined): value is string {
  if (!value) return false;

  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch {
    return false;
  }
}

function readCitations(value: unknown): Citation[] {
  if (!Array.isArray(value)) return [];

  return value.filter(isRecord).map((citation) => ({
    title: nonemptyString(citation.title),
    url: nonemptyString(citation.url),
    locator: nonemptyString(citation.locator),
  }));
}

function hasCompleteCitation(citation: Citation): boolean {
  return Boolean(citation.title && isHttpUrl(citation.url) && citation.locator);
}

function renderCitation(citation: Citation, index: number) {
  return (
    <li key={`${citation.url ?? citation.title ?? 'source'}-${index}`}>
      {citation.title ? <strong>{citation.title}</strong> : null}
      {citation.url ? (
        <>
          {citation.title ? ' — ' : null}
          {isHttpUrl(citation.url) ? (
            <a href={citation.url} target="_blank" rel="noreferrer">
              {citation.url}
            </a>
          ) : (
            <span>{citation.url}</span>
          )}
        </>
      ) : null}
      {citation.locator ? <span> ({citation.locator})</span> : null}
    </li>
  );
}

export default function DeadlineAnswer({ response }: DeadlineAnswerProps) {
  if (!isRecord(response)) {
    return (
      <section aria-live="polite">
        <h2>Deadline response</h2>
        <p>I couldn't read a response. Please try again.</p>
      </section>
    );
  }

  const outcome = nonemptyString(response.outcome);
  const message = nonemptyString(response.message);
  const citations = readCitations(response.citations);

  if (outcome === 'needs_context') {
    const requiredContext = Array.isArray(response.requiredContext)
      ? response.requiredContext.filter((item): item is string => typeof item === 'string')
      : [];
    const needsTerm = requiredContext.includes('term');

    return (
      <section aria-live="polite">
        <h2>{needsTerm ? 'Which academic term do you mean?' : 'More context needed'}</h2>
        <p>{message ?? (needsTerm
          ? 'Please provide the academic term so I can check the applicable deadline.'
          : 'Please provide the missing public context so I can check the deadline.')}</p>
      </section>
    );
  }

  if (outcome === 'escalation_required') {
    const escalation: Escalation = isRecord(response.escalation)
      ? {
          office: nonemptyString(response.escalation.office),
          contactUrl: nonemptyString(response.escalation.contactUrl),
        }
      : {};
    const office = escalation.office ?? 'the responsible university office';

    return (
      <section aria-live="polite">
        <h2>Check with an official source</h2>
        <p>
          I can't verify a current, complete deadline. Contact {office} for the
          official schedule.
        </p>
        {isHttpUrl(escalation.contactUrl) ? (
          <p>
            <a href={escalation.contactUrl} target="_blank" rel="noreferrer">
              Contact {office}
            </a>
          </p>
        ) : null}
      </section>
    );
  }

  if (outcome === 'answered') {
    const completeCitations = citations.filter(hasCompleteCitation);

    if (message && completeCitations.length > 0) {
      return (
        <section aria-live="polite">
          <h2>Deadline answer</h2>
          <p>{message}</p>
          <h3>Sources</h3>
          <ul>{citations.map(renderCitation)}</ul>
        </section>
      );
    }

    return (
      <section aria-live="polite">
        <h2>Deadline not verified</h2>
        <p>
          I can't safely display a deadline because the response is missing its
          answer or complete source details.
        </p>
        {citations.length > 0 ? (
          <>
            <h3>Available source details</h3>
            <ul>{citations.map(renderCitation)}</ul>
          </>
        ) : null}
      </section>
    );
  }

  if (outcome === 'cannot_verify') {
    return (
      <section aria-live="polite">
        <h2>Deadline not verified</h2>
        <p>I can't verify a current, complete deadline from reliable schedule information.</p>
      </section>
    );
  }

  return (
    <section aria-live="polite">
      <h2>Deadline response unavailable</h2>
      <p>I couldn't verify a deadline because the response did not include a recognized outcome.</p>
    </section>
  );
}
