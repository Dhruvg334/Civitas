const capabilities = [
  ["Understand", "Convert images, video, text, and location into structured evidence."],
  ["Connect", "Identify when separate reports describe the same real-world incident."],
  ["Prioritize", "Separate public harm from operational response urgency."],
  ["Verify", "Compare before-and-after evidence before an incident is closed."],
];

export default function HomePage() {
  return (
    <main>
      <section className="hero">
        <span className="eyebrow">Evidence-backed civic intelligence</span>
        <h1>Civitas</h1>
        <p>
          Turning every civic report into clear, accountable action. Civitas structures evidence,
          detects duplicate incidents, grounds decisions in policy, and keeps important outcomes
          reviewable by people.
        </p>
        <div className="grid">
          {capabilities.map(([title, body]) => (
            <article className="card" key={title}>
              <h2>{title}</h2>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
