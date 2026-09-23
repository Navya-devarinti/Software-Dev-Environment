type PolicyAnswerProps = {
  message: string;
};

export default function PolicyAnswer({ message }: PolicyAnswerProps) {
  return (
    <section>
      <h2>Policy guidance</h2>
      <p>{message}</p>
    </section>
  );
}
