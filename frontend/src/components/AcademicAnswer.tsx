type AcademicAnswerProps = {
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

const ACADEMIC_CONTEXT_FIELDS = new Set([
  'campus',
  'term',
  'program',
  'courseCode',
  'academicLevel',
]);

const INDIVIDUAL_CLAIMS = [
  'you will graduate',
  "you won't graduate",
  'you will not graduate',
  'you can graduate',
  'you cannot graduate',
  "you can't graduate",
  'you are eligible',
  'you are not eligible',
  'you qualify to graduate',
  'you do not qualify to graduate',
  'you meet all requirements',
  'you do not meet all requirements',
  'you are approved',
  'you have been approved',
  'you are denied',
  'you have been denied',
  'approved to graduate',
  'denied graduation',
  'you have completed enough credits',
  "you've completed enough credits",
  'your graduation status is',
  'you meet the graduation requirements',
  'you do not meet the graduation requirements',
];

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

function containsIndividualClaim(value: string): boolean {
  const normalized = value.toLowerCase();
  return INDIVIDUAL_CLAIMS.some((claim) => normalized.includes(claim));
}

function readCitations(value: unknown): Citation[] {
  if (!Array.isArray(value)) return [];

  return value
    .filter(isRecord)
    .map((citation) => ({
      title: nonemptyString(citation.title),
      url: nonemptyString(citation.url),
      locator: nonemptyString(citation.locator),
    }))
    .filter(
      (citation) => citation.title !== undefined && citation.url !== undefined,
    );
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

function renderNextSteps(value: unknown) {
  if (!Array.isArray(value)) return null;
  const steps = value
    .map(nonemptyString)
    .filter((step): step is string => step !== undefined);
  if (steps.length === 0) return null;

  return (
    <>
      <h3>Next steps</h3>
      <ul>
        {steps.map((step, index) => (
          <li key={`${step}-${index}`}>{step}</li>
        ))}
      </ul>
    </>
  );
}

export default function AcademicAnswer({ response }: AcademicAnswerProps) {
  if (!isRecord(response)) {
    return (
      <section aria-live="polite">
        <h2>Academic response</h2>
        <p>I couldn't read an academic response. Please try again.</p>
      </section>
    );
  }

  const outcome = nonemptyString(response.outcome);
  const message = nonemptyString(response.message);
  const citations = readCitations(response.citations);

  if (outcome === 'needs_context') {
    const fields = Array.isArray(response.requiredContext)
      ? response.requiredContext.filter(
          (field): field is string =>
            typeof field === 'string' && ACADEMIC_CONTEXT_FIELDS.has(field),
        )
      : [];
    return (
      <section aria-live="polite">
        <h2>More academic context needed</h2>
        <p>
          {message ??
            'Please provide the missing public academic context before I can answer.'}
        </p>
        {fields.length > 0 ? (
          <p>Needed context: {fields.join(', ')}</p>
        ) : null}
      </section>
    );
  }

  if (outcome === 'answered') {
    if (!message || containsIndividualClaim(message) || citations.length === 0) {
      return (
        <section aria-live="polite">
          <h2>Academic information not verified</h2>
          <p>
            I can't safely display an academic answer without supported
            explanation and official source citations.
          </p>
        </section>
      );
    }

    return (
      <section aria-live="polite">
        <h2>Academic guidance</h2>
        <p>{message}</p>
        {renderNextSteps(response.nextSteps)}
        <h3>Sources</h3>
        <ul>{citations.map(renderCitation)}</ul>
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
    const office = escalation.office ?? 'Academic Advising';
    const confirmsNoIndividualDecision =
      message?.toLowerCase().includes("can't determine an individual") ||
      message?.toLowerCase().includes('cannot determine an individual');
    const safeMessage =
      message &&
      confirmsNoIndividualDecision &&
      !containsIndividualClaim(message)
        ? message
        : undefined;
    const safeCitations = safeMessage && citations.length > 0 ? citations : [];

    return (
      <section aria-live="polite">
        <h2>Academic advising referral</h2>
        <p>
          {safeMessage ??
            "I can't determine an individual academic or graduation outcome from public information. Please contact Academic Advising for review."}
        </p>
        <p>
          <strong>{office}</strong>
        </p>
        {escalation.reason ? <p>{escalation.reason}</p> : null}
        {isHttpUrl(escalation.contactUrl) ? (
          <p>
            <a href={escalation.contactUrl} target="_blank" rel="noreferrer">
              Contact {office}
            </a>
          </p>
        ) : null}
        {safeCitations.length > 0 ? (
          <>
            <h3>Relevant sources</h3>
            <ul>{safeCitations.map(renderCitation)}</ul>
          </>
        ) : null}
      </section>
    );
  }

  if (outcome === 'cannot_verify') {
    return (
      <section aria-live="polite">
        <h2>Academic information not verified</h2>
        <p>
          {message && !containsIndividualClaim(message)
            ? message
            : "I can't verify a complete, current academic answer from official catalog evidence."}
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

  return (
    <section aria-live="polite">
      <h2>Academic response unavailable</h2>
      <p>
        I couldn't verify this academic information because the response did not
        include a recognized outcome.
      </p>
    </section>
  );
}
