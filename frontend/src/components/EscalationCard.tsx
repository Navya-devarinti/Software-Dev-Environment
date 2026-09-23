type EscalationCardProps = {
  office: string;
  reason: string;
  contactUrl?: string;
};

export default function EscalationCard({ office, reason, contactUrl }: EscalationCardProps) {
  return (
    <section>
      <h2>Route to official support</h2>
      <p>
        <strong>{office}</strong>
      </p>
      <p>{reason}</p>
      {contactUrl ? <a href={contactUrl}>Office contact</a> : null}
    </section>
  );
}
