type DeadlineAnswerProps = {
  message: string;
  term?: string;
};

export default function DeadlineAnswer({ message, term }: DeadlineAnswerProps) {
  return (
    <section>
      <h2>Deadline</h2>
      <p>{message}</p>
      {term ? <small>Term: {term}</small> : null}
    </section>
  );
}
