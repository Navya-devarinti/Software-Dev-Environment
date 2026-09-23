type RapidUpdateAnswerProps = {
  message: string;
};

export default function RapidUpdateAnswer({ message }: RapidUpdateAnswerProps) {
  return (
    <section>
      <h2>Rapid campus update</h2>
      <p>{message}</p>
    </section>
  );
}
