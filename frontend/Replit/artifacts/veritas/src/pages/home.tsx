import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  Fragment,
} from "react";
import {
  useGetExampleQuestions,
  useSynthesizeAnswer,
} from "@workspace/api-client-react";
import type {
  ExampleQuestion,
  VeritasAnswer,
  VeritasIdea,
  VeritasSource,
} from "@workspace/api-client-react";

// ─── Types ──────────────────────────────────────────────────────────────────

type KnowledgeType = "docs" | "practice" | "failure";

// ─── Type helpers ────────────────────────────────────────────────────────────

function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

// ─── Source type styles ──────────────────────────────────────────────────────

const TYPE_STYLE: Record<
  KnowledgeType,
  { dot: string; label: string; text: string }
> = {
  docs: {
    dot: "bg-blue-500",
    label: "text-blue-400/90",
    text: "Spec",
  },
  practice: {
    dot: "bg-amber-500",
    label: "text-amber-400/90",
    text: "Practice",
  },
  failure: {
    dot: "bg-rose-500",
    label: "text-rose-400/90",
    text: "Failure",
  },
};

// ─── Inline code ─────────────────────────────────────────────────────────────

function IC({ children }: { children: React.ReactNode }) {
  return (
    <code className="text-[12.5px] font-mono text-slate-200 bg-slate-800/60 border border-slate-700/40 px-[5px] py-[1px] rounded-[3px] mx-[1px] leading-none">
      {children}
    </code>
  );
}

// ─── Citation ────────────────────────────────────────────────────────────────

function Cite({
  id,
  children,
  onEnter,
  onLeave,
  active,
}: {
  id: string;
  children: React.ReactNode;
  onEnter: (id: string) => void;
  onLeave: () => void;
  active: boolean;
}) {
  return (
    <span
      className={cn(
        "inline font-mono text-[10px] ml-[2px] px-[4px] py-[1.5px] rounded cursor-pointer transition-all duration-150 border align-baseline select-none",
        active
          ? "text-slate-100 bg-slate-700/70 border-slate-600/60 no-underline"
          : "text-slate-500 bg-transparent border-transparent underline decoration-dotted underline-offset-[3px] decoration-slate-600/80 hover:text-slate-300 hover:bg-slate-800/50 hover:border-slate-700/40 hover:no-underline"
      )}
      onMouseEnter={() => onEnter(id)}
      onMouseLeave={onLeave}
    >
      {children}
    </span>
  );
}

// ─── Paragraph parser ────────────────────────────────────────────────────────

function parseContent(
  text: string,
  sources: Record<string, VeritasSource>,
  onEnterCite: (id: string) => void,
  onLeaveCite: () => void,
  activeCiteId: string | null
): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /`([^`]+)`|\[([^\]]+)\]/g;
  let lastIndex = 0;
  let i = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<Fragment key={`t-${i++}`}>{text.slice(lastIndex, match.index)}</Fragment>);
    }

    if (match[1] !== undefined) {
      parts.push(<IC key={`c-${i++}`}>{match[1]}</IC>);
    } else if (match[2] !== undefined) {
      const citeId = match[2];
      const src = sources[citeId];
      if (src) {
        parts.push(
          <Cite
            key={`s-${i++}`}
            id={citeId}
            onEnter={onEnterCite}
            onLeave={onLeaveCite}
            active={activeCiteId === citeId}
          >
            {src.short}
          </Cite>
        );
      } else {
        parts.push(<Fragment key={`u-${i++}`}>{match[0]}</Fragment>);
      }
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(<Fragment key={`t-${i++}`}>{text.slice(lastIndex)}</Fragment>);
  }

  return parts;
}

// ─── Divider ─────────────────────────────────────────────────────────────────

function Divider() {
  return (
    <div className="h-px w-full bg-gradient-to-r from-slate-800/80 via-slate-800/40 to-transparent my-14" />
  );
}

// ─── Reading view ─────────────────────────────────────────────────────────────

function ReadingView({
  answer,
  onReset,
}: {
  answer: VeritasAnswer;
  onReset: () => void;
}) {
  const [activeIdeaIndex, setActiveIdeaIndex] = useState(0);
  const [hoveredCiteId, setHoveredCiteId] = useState<string | null>(null);
  const [panelVisible, setPanelVisible] = useState(true);
  const prevPanelKey = useRef<string>("idea-0");
  const scrollRef = useRef<HTMLDivElement>(null);

  const ideas: VeritasIdea[] = answer.ideas ?? [];
  const sources: Record<string, VeritasSource> = answer.sources ?? {};

  // Precompute threshold offsets based on idea count
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const top = e.currentTarget.scrollTop;
      const thresholds = ideas.map((_, i) => 340 + i * 400);
      let idx = 0;
      for (let i = 0; i < thresholds.length - 1; i++) {
        if (top >= thresholds[i]) idx = i + 1;
      }
      setActiveIdeaIndex(Math.min(idx, ideas.length - 1));
    },
    [ideas]
  );

  const onEnterCite = useCallback((id: string) => setHoveredCiteId(id), []);
  const onLeaveCite = useCallback(() => setHoveredCiteId(null), []);

  const panelKey = hoveredCiteId ?? `idea-${activeIdeaIndex}`;
  useEffect(() => {
    if (prevPanelKey.current === panelKey) return;
    prevPanelKey.current = panelKey;
    setPanelVisible(false);
    const t = setTimeout(() => setPanelVisible(true), 90);
    return () => clearTimeout(t);
  }, [panelKey]);

  const activeIdea = ideas[activeIdeaIndex];
  const activeSources = (activeIdea?.sourceIds ?? [])
    .map((id) => ({ id, ...(sources[id] ?? {}) }))
    .filter((s) => s.label);
  const hoveredSource = hoveredCiteId ? sources[hoveredCiteId] : null;

  const allSources = Object.values(sources);
  const totalSources = allSources.length;

  return (
    <div className="min-h-screen bg-[#07090F] text-slate-300 font-sans selection:bg-slate-800/70 flex overflow-hidden">
      {/* Reading column */}
      <div
        ref={scrollRef}
        className="flex-1 h-screen overflow-y-auto overflow-x-hidden"
        onScroll={handleScroll}
      >
        <div className="max-w-[660px] mx-auto py-20 px-8 lg:px-0">
          {/* Header */}
          <header className="mb-16">
            <div className="flex items-center gap-3 mb-5">
              <button
                onClick={onReset}
                className="text-[9px] font-mono tracking-[0.28em] text-slate-700 uppercase hover:text-slate-500 transition-colors cursor-pointer"
              >
                ← New question
              </button>
            </div>
            <p className="text-[9px] font-mono tracking-[0.32em] text-slate-700 uppercase mb-4">
              veritas · technical synthesis
            </p>
            <h1 className="text-[24px] font-semibold text-slate-50 leading-snug tracking-tight max-w-[560px]">
              {answer.question}
            </h1>
            <p className="mt-3.5 text-[13px] text-slate-600 leading-relaxed max-w-[500px]">
              {ideas.length} concepts, each synthesized from spec, observed
              practice, and documented failure. Citations are inspectable —
              hover to see the source.
            </p>
          </header>

          {/* Ideas */}
          {ideas.map((idea, idx) => {
            const isActive = idx === activeIdeaIndex;
            return (
              <React.Fragment key={idea.id}>
                <article className="relative mb-0 pl-5 scroll-mt-20">
                  <div
                    className={cn(
                      "absolute left-0 top-1 bottom-1 w-[2px] rounded-full transition-all duration-500 ease-in-out",
                      isActive ? "bg-slate-600/60" : "bg-transparent"
                    )}
                  />
                  <h2 className="text-[10px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-3.5">
                    {String(idx + 1).padStart(2, "0")} · {idea.id.replace(/-/g, " ")}
                  </h2>
                  <p className="text-[14.5px] font-semibold text-slate-100 leading-snug mb-4 max-w-[560px] tracking-[-0.01em]">
                    {idea.concept}
                  </p>
                  <div className="text-[14px] leading-[1.88] text-slate-400 space-y-4 max-w-[580px]">
                    {idea.paragraphs.map((para, pi) => (
                      <p key={pi}>
                        {parseContent(
                          para,
                          sources,
                          onEnterCite,
                          onLeaveCite,
                          hoveredCiteId
                        )}
                      </p>
                    ))}
                  </div>
                </article>
                {idx < ideas.length - 1 && <Divider />}
              </React.Fragment>
            );
          })}

          <div className="h-28" />
        </div>
      </div>

      {/* Source map sidebar */}
      <aside className="w-[216px] shrink-0 border-l border-slate-800/30 hidden lg:flex flex-col pt-20 pb-8 px-5 bg-[#05060C]">
        <div className="sticky top-20 flex flex-col">
          {/* Concept navigator */}
          <div className="mb-7">
            <p className="text-[8.5px] font-mono tracking-[0.32em] text-slate-700 uppercase mb-4">
              Reading
            </p>
            <div className="space-y-1">
              {ideas.map((idea, i) => {
                const isActive = i === activeIdeaIndex;
                return (
                  <div
                    key={idea.id}
                    className={cn(
                      "flex items-start gap-2 py-1.5 pl-2 pr-1 rounded transition-all duration-300 ease-in-out",
                      isActive ? "bg-slate-800/30" : ""
                    )}
                  >
                    <span
                      className={cn(
                        "text-[9px] font-mono mt-[2.5px] shrink-0 transition-colors duration-300",
                        isActive ? "text-slate-400" : "text-slate-700"
                      )}
                    >
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span
                      className={cn(
                        "text-[10.5px] leading-snug transition-colors duration-300",
                        isActive ? "text-slate-300" : "text-slate-700"
                      )}
                    >
                      {idea.concept}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Source panel */}
          <div className="border-t border-slate-800/50 pt-5">
            <div className="flex items-center justify-between mb-3.5">
              <p className="text-[8.5px] font-mono tracking-[0.32em] text-slate-700 uppercase">
                {hoveredSource
                  ? "Inspecting"
                  : `Sources · ${String(activeIdeaIndex + 1).padStart(2, "0")}`}
              </p>
              {hoveredSource && (
                <div
                  className={cn(
                    "w-1.5 h-1.5 rounded-full",
                    TYPE_STYLE[hoveredSource.type as KnowledgeType]?.dot ?? "bg-slate-600"
                  )}
                />
              )}
            </div>

            <div
              className="transition-opacity duration-100 ease-in-out"
              style={{ opacity: panelVisible ? 1 : 0 }}
            >
              {hoveredSource ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "text-[8.5px] font-mono uppercase tracking-wider",
                        TYPE_STYLE[hoveredSource.type as KnowledgeType]?.label ?? "text-slate-500"
                      )}
                    >
                      {TYPE_STYLE[hoveredSource.type as KnowledgeType]?.text ?? hoveredSource.type}
                    </span>
                    <span className="text-[8.5px] font-mono text-slate-700">·</span>
                    <span className="text-[8.5px] font-mono text-slate-700">
                      {hoveredSource.meta}
                    </span>
                  </div>
                  <p className="text-[11.5px] text-slate-200 leading-snug font-medium">
                    {hoveredSource.label}
                  </p>
                  <div className="mt-3 pt-3 border-t border-slate-800/60">
                    <p className="text-[10.5px] text-slate-500 leading-relaxed font-mono">
                      "{hoveredSource.excerpt}"
                    </p>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="space-y-3 mb-4">
                    {activeSources.map((src) => (
                      <div key={src.id} className="flex items-start gap-2">
                        <div
                          className={cn(
                            "w-[5px] h-[5px] rounded-full shrink-0 mt-[4.5px]",
                            TYPE_STYLE[src.type as KnowledgeType]?.dot ?? "bg-slate-600"
                          )}
                        />
                        <div>
                          <span
                            className={cn(
                              "text-[8.5px] font-mono uppercase tracking-wide block mb-0.5",
                              TYPE_STYLE[src.type as KnowledgeType]?.label ?? "text-slate-500"
                            )}
                          >
                            {TYPE_STYLE[src.type as KnowledgeType]?.text ?? src.type}
                          </span>
                          <p className="text-[10.5px] text-slate-500 leading-snug">
                            {src.label}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-[8.5px] font-mono text-slate-700 leading-relaxed border-t border-slate-800/40 pt-3">
                    hover citations in the text to inspect any source
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Corpus footer */}
          {totalSources > 0 && (
            <div className="border-t border-slate-800/40 mt-6 pt-5">
              <div className="flex justify-between items-center mb-3">
                <span className="text-[8.5px] font-mono tracking-[0.2em] text-slate-700 uppercase">
                  Corpus
                </span>
                <span className="text-[11px] font-light text-slate-700 tabular-nums">
                  {totalSources} sources
                </span>
              </div>
              <div className="space-y-1.5">
                {(["docs", "practice", "failure"] as KnowledgeType[]).map(
                  (t) => {
                    const count = allSources.filter((s) => s.type === t).length;
                    if (count === 0) return null;
                    const pct = Math.round((count / totalSources) * 100);
                    return (
                      <div key={t} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <div
                              className={cn(
                                "w-[5px] h-[5px] rounded-full",
                                TYPE_STYLE[t].dot
                              )}
                            />
                            <span
                              className={cn(
                                "text-[8.5px] font-mono uppercase tracking-wide",
                                TYPE_STYLE[t].label
                              )}
                            >
                              {TYPE_STYLE[t].text}
                            </span>
                          </div>
                          <span className="text-[9px] font-mono text-slate-700">
                            {count}
                          </span>
                        </div>
                        <div className="h-[2px] rounded-full bg-slate-800/60 overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full opacity-50",
                              TYPE_STYLE[t].dot
                            )}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

// ─── Ask / empty view ────────────────────────────────────────────────────────

function AskView({
  onSubmit,
  isLoading,
  error,
  examples,
}: {
  onSubmit: (q: string) => void;
  isLoading: boolean;
  error: string | null;
  examples: ExampleQuestion[];
}) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (q.length >= 5) onSubmit(q);
  };

  return (
    <div className="min-h-screen bg-[#07090F] text-slate-300 font-sans flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-[620px]">
        {/* Brand */}
        <div className="mb-12 text-center">
          <p className="text-[9px] font-mono tracking-[0.4em] text-slate-700 uppercase mb-5">
            veritas
          </p>
          <h1 className="text-[28px] font-semibold text-slate-100 leading-tight tracking-tight">
            Ask a technical question.
          </h1>
          <p className="mt-3 text-[14px] text-slate-600 leading-relaxed max-w-[420px] mx-auto">
            Each answer is constructed from official docs, observed practice,
            and documented failure — synthesized into a single reading document.
          </p>
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="How do I stream tool use responses in Claude?"
              disabled={isLoading}
              className="w-full bg-slate-900/60 border border-slate-800/80 text-slate-200 placeholder:text-slate-700 rounded-lg px-4 py-3.5 text-[14px] font-sans outline-none focus:border-slate-600/80 transition-colors duration-150 pr-24 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || input.trim().length < 5}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 text-[11px] font-mono px-3 py-1.5 rounded-md transition-colors duration-150 cursor-pointer"
            >
              {isLoading ? "Thinking..." : "Synthesize →"}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-[12px] text-rose-500/80 font-mono">{error}</p>
          )}
        </form>

        {/* Loading state */}
        {isLoading && (
          <div className="mb-8 flex items-center gap-3">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1 h-1 bg-slate-600 rounded-full animate-pulse"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
            <span className="text-[11px] font-mono text-slate-700">
              Synthesizing from docs, practice, and failure cases...
            </span>
          </div>
        )}

        {/* Example questions */}
        {!isLoading && examples.length > 0 && (
          <div>
            <p className="text-[9px] font-mono tracking-[0.3em] text-slate-800 uppercase mb-4">
              Examples
            </p>
            <div className="space-y-2">
              {examples.map((ex) => (
                <button
                  key={ex.id}
                  onClick={() => {
                    setInput(ex.question);
                    setTimeout(() => onSubmit(ex.question), 0);
                  }}
                  disabled={isLoading}
                  className="w-full text-left group flex items-start gap-3 py-3 px-4 rounded-lg border border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900/40 transition-all duration-150 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <div className="shrink-0 mt-[3px] w-1 h-1 rounded-full bg-slate-700 group-hover:bg-slate-500 transition-colors" />
                  <div>
                    <p className="text-[13px] text-slate-400 group-hover:text-slate-300 transition-colors leading-snug">
                      {ex.question}
                    </p>
                    <p className="text-[11px] text-slate-700 font-mono mt-0.5">
                      {ex.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer note */}
        <div className="mt-16 flex items-center gap-6 justify-center">
          {(["docs", "practice", "failure"] as KnowledgeType[]).map((t) => (
            <div key={t} className="flex items-center gap-1.5">
              <div
                className={cn(
                  "w-1.5 h-1.5 rounded-full opacity-60",
                  TYPE_STYLE[t].dot
                )}
              />
              <span className="text-[9.5px] font-mono text-slate-700 uppercase tracking-wide">
                {TYPE_STYLE[t].text}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Home page ────────────────────────────────────────────────────────────────

export function Home() {
  const [answer, setAnswer] = useState<VeritasAnswer | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { data: examples = [] } = useGetExampleQuestions();

  const mutation = useSynthesizeAnswer({
    mutation: {
      onSuccess: (data) => {
        setAnswer(data);
        setSubmitError(null);
      },
      onError: () => {
        setSubmitError("Something went wrong synthesizing your answer. Please try again.");
      },
    },
  });

  const handleSubmit = useCallback(
    (question: string) => {
      setSubmitError(null);
      mutation.mutate({ data: { question } });
    },
    [mutation]
  );

  const handleReset = useCallback(() => {
    setAnswer(null);
    setSubmitError(null);
    mutation.reset();
  }, [mutation]);

  if (answer) {
    return <ReadingView answer={answer} onReset={handleReset} />;
  }

  return (
    <AskView
      onSubmit={handleSubmit}
      isLoading={mutation.isPending}
      error={submitError}
      examples={examples}
    />
  );
}
