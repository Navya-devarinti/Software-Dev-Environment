type PolicyAnswerProps = {
  response?: unknown;
};

type Citation = {
  title?: string;
  url?: string;
  locator?: string;
};

type Escalation = {
  office?: string;
  reason?: string;
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

export default function PolicyAnswer({ response }: PolicyAnswerProps) {
  if (!isRecord(response)) {
    return (
      <section aria-live="polite">
        <h2>Policy response</h2>
        <p>I couldn't read a policy response. Please try again.</p>
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
    const messageText = message ?? 'Please provide the missing public context so I can answer accurately.';

    return (
      <section aria-live="polite">
        <h2>{requiredContext.length > 0 ? 'More context needed' : 'Policy needs context'}</h2>
        <p>{messageText}</p>
      </section>
    );
  }

  if (outcome === 'escalation_required') {
    const escalation: Escalation = isRecord(response.escalation)
      ? {
          office: nonemptyString(response.escalation.office),
          reason: nonemptyString(response.escalation.reason),
          contactUrl: nonemptyString(response.escalation.contactUrl),
        }
      : {};

    const office = escalation.office ?? 'the responsible university office';
    const reason = escalation.reason ?? 'An individual outcome cannot be determined from the general public information alone.';
    const contactUrl = escalation.contactUrl;

    return (
      <section aria-live="polite">
        <h2>Contact the responsible office</h2>
        <p>
          {message ?? `General published guidance is available, but I can't determine an individual outcome. Please contact ${office}.`}
        </p>
        <p>
          <strong>{office}</strong>
        </p>
        <p>{reason}</p>
        {isHttpUrl(contactUrl) ? (
          <p>
            <a href={contactUrl} target="_blank" rel="noreferrer">
              Contact {office}
            </a>
          </p>
        ) : null}
        {citations.length > 0 ? (
          <>
            <h3>Relevant sources</h3>
            <ul>{citations.map(renderCitation)}</ul>
          </>
        ) : null}
      </section>
    );
  }

  if (outcome === 'answered') {
    if (!message || citations.length === 0) {
      return (
        <section aria-live="polite">
          <h2>Policy not verified</h2>
          <p>I can't verify the policy explanation from reliable official evidence.</p>
        </section>
      );
    }

    return (
      <section aria-live="polite">
        <h2>Policy guidance</h2>
        <p>{message}</p>
        <h3>Sources</h3>
        <ul>{citations.map(renderCitation)}</ul>
      </section>
    );
  }

  if (outcome === 'cannot_verify') {
    return (
      <section aria-live="polite">
        <h2>Policy not verified</h2>
        <p>{message ?? "I can't verify a current, complete policy or procedure from reliable official evidence."}</p>
        {citations.length > 0 ? (
          <>
            <h3>Available source details</h3>
            <ul>{citations.map(renderCitation)}</ul>
          </>
        ) : null}
      </section>
    );
  }

  return (
    <section aria-live="polite">
      <h2>Policy response unavailable</h2>
      <p>I couldn't verify this policy because the response did not include a recognized outcome.</p>
    </section>
  );
}
