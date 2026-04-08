interface AnswerSection {
  title: string;
  content: string;
  tier: number;
  citations: number[];
}

interface AnswerDisplayProps {
  sections: AnswerSection[];
}

const sectionStyles: Record<string, string> = {
  "Core Answer": "bg-zinc-900/70 border border-zinc-800",
  "Implementation Insight": "bg-blue-950/20 border border-blue-900/40",
  "Common Pitfalls": "bg-zinc-900 border-l-4 border-amber-400 shadow-[0_0_0_1px_rgba(255,255,255,0.04)]",
};

export function AnswerDisplay({ sections }: AnswerDisplayProps) {
  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-10 space-y-6 text-left">
      {sections.map((section) => (
        <section
          key={section.title}
          className={`rounded-2xl p-6 md:p-7 ${sectionStyles[section.title] ?? "bg-zinc-900/70 border border-zinc-800"}`}
        >
          <h3 className="text-lg md:text-xl font-semibold text-zinc-100 mb-4">
            {section.title}
          </h3>

          <div className="space-y-4 text-zinc-300 leading-8 text-[17px]">
            {section.content.split("\n\n").map((block, idx) => {
              const trimmed = block.trim();

              const isBulletBlock = trimmed.startsWith("•") || trimmed.includes("\n•");

              const isAnchorLine =
                trimmed.startsWith("**The pattern across all of these:") ||
                trimmed.startsWith("**Key takeaway:");

              if (isAnchorLine) {
                return (
                  <p key={idx} className="font-semibold text-zinc-100">
                    {trimmed.replace(/\*\*/g, "")}
                  </p>
                );
              }

              if (isBulletBlock) {
                return (
                  <div key={idx} className="space-y-3">
                    {trimmed.split("\n").map((line, lineIdx) => (
                      <p key={lineIdx} className="text-zinc-300">
                        {line}
                      </p>
                    ))}
                  </div>
                );
              }

              return (
                <p key={idx} className="text-zinc-300">
                  {trimmed}
                </p>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
