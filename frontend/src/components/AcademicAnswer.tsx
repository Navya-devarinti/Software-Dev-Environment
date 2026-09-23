type AcademicAnswerProps = {
  message: string;
};

export default function AcademicAnswer({ message }: AcademicAnswerProps) {
  return (
    <section>
      <h2>Academic guidance</h2>
      <p>{message}</p>
    </section>
  );
}
