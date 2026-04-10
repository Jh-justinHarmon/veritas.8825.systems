import React, { useState, useRef, useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";

// ─── Types ──────────────────────────────────────────────────────────────────

type KnowledgeType = "docs" | "practice" | "failure";

interface Source {
  label: string;
  short: string;
  type: KnowledgeType;
  meta: string;
  excerpt: string;
}

interface Idea {
  id: string;
  concept: string;
  sourceIds: string[];
}

// ─── Data ────────────────────────────────────────────────────────────────────

const SOURCES: Record<string, Source> = {
  "anthropic-docs-stream": {
    label: "Anthropic API Reference",
    short: "anthropic.com/docs",
    type: "docs",
    meta: "v1.4 · March 2025",
    excerpt: "content_block_start → content_block_delta (input_json_delta) → content_block_stop",
  },
  "anthropic-docs-stop": {
    label: "Anthropic API Reference — stop_reason",
    short: "anthropic.com/docs",
    type: "docs",
    meta: "v1.4 · March 2025",
    excerpt: "stop_reason: 'tool_use' indicates the model is requesting a tool call",
  },
  "sdk-ts": {
    label: "anthropic-sdk-typescript",
    short: "github.com/anthropics",
    type: "practice",
    meta: "current",
    excerpt: "stream.on('contentBlock', block => { if (block.type === 'tool_use') ... })",
  },
  "willison": {
    label: "Simon Willison's Weblog",
    short: "simonwillison.net",
    type: "practice",
    meta: "2024",
    excerpt: "The SDK's contentBlock event is the idiomatic way to handle tool use streaming.",
  },
  "hn-39482103": {
    label: "Hacker News Discussion",
    short: "news.ycombinator.com · #39482103",
    type: "practice",
    meta: "2024",
    excerpt: "Consensus: use .stream() + contentBlock, never parse raw chunks manually.",
  },
  "sdk-py-847": {
    label: "anthropic-sdk-python · issue #847",
    short: "github.com/anthropics",
    type: "failure",
    meta: "2024",
    excerpt: "json.JSONDecodeError when parsing partial input_json_delta chunks directly.",
  },
  "so-stop-reason": {
    label: "Stack Overflow",
    short: "stackoverflow.com",
    type: "failure",
    meta: "2024",
    excerpt: "stop_reason check omitted — handler executes before tool_use is confirmed.",
  },
  "forum-maxtokens": {
    label: "Anthropic Community Forum",
    short: "community.anthropic.com",
    type: "failure",
    meta: "March 2025",
    excerpt: "max_tokens exhausted mid-call produces incomplete JSON with no explicit error.",
  },
};

const IDEAS: Idea[] = [
  {
    id: "protocol",
    concept: "Streaming tool use runs on a distinct event protocol",
    sourceIds: ["anthropic-docs-stream", "sdk-ts", "willison"],
  },
  {
    id: "accumulation",
    concept: "Tool arguments arrive in fragments — parse only after the final event",
    sourceIds: ["anthropic-docs-stream", "sdk-ts", "sdk-py-847", "hn-39482103"],
  },
  {
    id: "execution-gate",
    concept: "Execution requires a specific state condition, not just stream completion",
    sourceIds: ["anthropic-docs-stop", "so-stop-reason"],
  },
  {
    id: "budget",
    concept: "Token budget exhaustion silently corrupts mid-call",
    sourceIds: ["forum-maxtokens", "hn-39482103"],
  },
];

// ─── Source type colors ──────────────────────────────────────────────────────

const TYPE_STYLE: Record<KnowledgeType, { dot: string; ring: string; label: string; text: string }> = {
  docs:     { dot: "bg-blue-500",  ring: "ring-blue-500/30",  label: "text-blue-400/90",  text: "Spec" },
  practice: { dot: "bg-amber-500", ring: "ring-amber-500/30", label: "text-amber-400/90", text: "Practice" },
  failure:  { dot: "bg-rose-500",  ring: "ring-rose-500/30",  label: "text-rose-400/90",  text: "Failure" },
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function IC({ children }: { children: React.ReactNode }) {
  return (
    <code className="text-[12.5px] font-mono text-slate-200 bg-slate-800/60 border border-slate-700/40 px-[5px] py-[1px] rounded-[3px] mx-[1px] leading-none">
      {children}
    </code>
  );
}

function Cite({
  id,
  children,
  onEnter,
  onLeave,
  active,
}: {
  id: string;
  children?: React.ReactNode;
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
      {children ?? id}
    </span>
  );
}

function CodeBlock({ code }: { code: string }) {
  const keywords = ["const", "await", "if", "return", "async", "function"];
  const props = ["model", "max_tokens", "messages", "role", "content", "tools", "stream", "type", "name", "input"];

  return (
    <pre className="text-[12.5px] font-mono leading-[1.65] whitespace-pre text-slate-300 bg-[#090C14] border border-slate-800/60 px-5 py-4 rounded overflow-x-auto mt-5 mb-1">
      {code.split("\n").map((line, i) => (
        <div key={i} className="leading-6">
          {line.startsWith("  //") || line.startsWith("//") ? (
            <span className="text-slate-600 italic">{line}</span>
          ) : (
            line.split(/('[\s\S]*?')/g).map((part, j) => {
              if (part.startsWith("'") && part.endsWith("'")) {
                return <span key={j} className="text-emerald-400">{part}</span>;
              }
              const kwParts = part.split(/\b(const|await|if|return|async|function|model|max_tokens|messages|role|content|tools|stream|type|name|input)\b/g);
              return kwParts.map((kp, k) => {
                if (keywords.includes(kp)) return <span key={k} className="text-violet-400">{kp}</span>;
                if (props.includes(kp)) return <span key={k} className="text-sky-300">{kp}</span>;
                return <span key={k} className="text-slate-300">{kp}</span>;
              });
            })
          )}
        </div>
      ))}
    </pre>
  );
}

// ─── Divider ─────────────────────────────────────────────────────────────────

function Divider() {
  return <div className="h-px w-full bg-gradient-to-r from-slate-800/80 via-slate-800/40 to-transparent my-14" />;
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function VeritasApp() {
  const [activeIdeaIndex, setActiveIdeaIndex] = useState(0);
  const [hoveredCiteId, setHoveredCiteId] = useState<string | null>(null);
  // Fade signal for the source panel when its content changes
  const [panelVisible, setPanelVisible] = useState(true);
  const prevPanelKey = useRef<string>("idea-0");
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const top = e.currentTarget.scrollTop;
    if (top < 340) setActiveIdeaIndex(0);
    else if (top < 720) setActiveIdeaIndex(1);
    else if (top < 1050) setActiveIdeaIndex(2);
    else setActiveIdeaIndex(3);
  }, []);

  const onEnter = useCallback((id: string) => setHoveredCiteId(id), []);
  const onLeave = useCallback(() => setHoveredCiteId(null), []);

  // Fade out → in when panel key changes
  const panelKey = hoveredCiteId ?? `idea-${activeIdeaIndex}`;
  useEffect(() => {
    if (prevPanelKey.current === panelKey) return;
    prevPanelKey.current = panelKey;
    setPanelVisible(false);
    const t = setTimeout(() => setPanelVisible(true), 90);
    return () => clearTimeout(t);
  }, [panelKey]);

  const c = (id: string) => (
    <Cite id={id} onEnter={onEnter} onLeave={onLeave} active={hoveredCiteId === id}>
      {SOURCES[id]?.short ?? id}
    </Cite>
  );

  const activeIdea = IDEAS[activeIdeaIndex];
  const activeSources = activeIdea.sourceIds.map((id) => ({ id, ...SOURCES[id] }));
  const hoveredSource = hoveredCiteId ? SOURCES[hoveredCiteId] : null;

  return (
    <div className="min-h-screen bg-[#07090F] text-slate-300 font-sans selection:bg-slate-800/70 flex overflow-hidden">

      {/* ── Reading column ── */}
      <div
        ref={scrollRef}
        className="flex-1 h-screen overflow-y-auto overflow-x-hidden"
        onScroll={handleScroll}
      >
        <div className="max-w-[660px] mx-auto py-20 px-10 lg:px-0">

          {/* Header */}
          <header className="mb-16">
            <p className="text-[9px] font-mono tracking-[0.32em] text-slate-700 uppercase mb-4">
              veritas · technical synthesis
            </p>
            <h1 className="text-[25px] font-semibold text-slate-50 leading-snug tracking-tight max-w-[560px]">
              How do I stream tool use responses in Claude?
            </h1>
            <p className="mt-3.5 text-[13px] text-slate-600 leading-relaxed max-w-[500px]">
              Four concepts, each synthesized from spec, observed practice, and documented failure.
              Citations are inspectable — hover to see the source.
            </p>
          </header>

          {/* ── Idea 1: Protocol ── */}
          <article
            className={cn(
              "relative mb-0 pl-5 scroll-mt-20 transition-all duration-300",
            )}
            data-idea="protocol"
          >
            {/* Active article left accent */}
            <div className={cn(
              "absolute left-0 top-1 bottom-1 w-[2px] rounded-full transition-all duration-500 ease-in-out",
              activeIdeaIndex === 0 ? "bg-slate-600/60" : "bg-transparent"
            )} />
            <h2 className="text-[10px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-3.5">
              01 · Event protocol
            </h2>
            <p className="text-[14.5px] font-semibold text-slate-100 leading-snug mb-4 max-w-[560px] tracking-[-0.01em]">
              Streaming tool use runs on a distinct event protocol — not raw text chunks.
            </p>
            <div className="text-[14px] leading-[1.88] text-slate-400 space-y-4 max-w-[580px]">
              <p>
                When you set <IC>stream: true</IC> on a request that may invoke a tool,
                the API emits a three-event sequence: <IC>content_block_start</IC> with{" "}
                <IC>type: "tool_use"</IC>, a series of <IC>content_block_delta</IC>{" "}
                events each carrying an <IC>input_json_delta</IC> fragment, then{" "}
                <IC>content_block_stop</IC>. {c("anthropic-docs-stream")}
              </p>
              <p>
                In practice most teams never encounter this sequence directly — the TypeScript SDK's{" "}
                <IC>.stream()</IC> method aggregates it internally and fires a single{" "}
                <IC>contentBlock</IC> event with a fully resolved <IC>block.input</IC>.{" "}
                {c("sdk-ts")} {c("willison")} This is the idiomatic path: handling
                raw delta events is rarely necessary and significantly more error-prone.
              </p>
            </div>
          </article>

          <Divider />

          {/* ── Idea 2: Accumulation ── */}
          <article
            className="relative mb-0 pl-5 scroll-mt-20"
            data-idea="accumulation"
          >
            <div className={cn(
              "absolute left-0 top-1 bottom-1 w-[2px] rounded-full transition-all duration-500 ease-in-out",
              activeIdeaIndex === 1 ? "bg-slate-600/60" : "bg-transparent"
            )} />
            <h2 className="text-[10px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-3.5">
              02 · JSON accumulation
            </h2>
            <p className="text-[14.5px] font-semibold text-slate-100 leading-snug mb-4 max-w-[560px] tracking-[-0.01em]">
              Tool arguments arrive in fragments. Parse only after the final event.
            </p>
            <div className="text-[14px] leading-[1.88] text-slate-400 space-y-4 max-w-[580px]">
              <p>
                Each <IC>input_json_delta</IC> is a deliberately incomplete JSON substring.
                The spec is explicit: you must concatenate every fragment before calling{" "}
                <IC>JSON.parse</IC>, and only after <IC>content_block_stop</IC> fires.{" "}
                {c("anthropic-docs-stream")} Calling <IC>JSON.parse</IC> on any earlier
                fragment throws <IC>SyntaxError</IC> — the most common mistake from developers
                who've worked with text streaming, where each chunk is self-contained. {c("sdk-py-847")}
              </p>
              <p>
                The SDK enforces this contract automatically: <IC>block.input</IC> in the{" "}
                <IC>contentBlock</IC> event is already fully assembled. {c("sdk-ts")} Community
                consensus is to use <IC>.stream()</IC> and <IC>contentBlock</IC> exclusively —
                not raw delta handling — specifically to avoid this class of error. {c("hn-39482103")}
              </p>
            </div>

            <CodeBlock code={`const stream = await anthropic.messages.stream({
  model: 'claude-3-5-sonnet-20240620',
  max_tokens: 4096,
  messages: [{ role: 'user', content: 'What is the weather in SF?' }],
  tools: [weatherTool]
});

stream.on('contentBlock', (block) => {
  // block.input is fully assembled here — safe to use
  if (block.type === 'tool_use') executeTool(block.name, block.input);
});`} />
          </article>

          <Divider />

          {/* ── Idea 3: Execution gate ── */}
          <article
            className="relative mb-0 pl-5 scroll-mt-20"
            data-idea="execution-gate"
          >
            <div className={cn(
              "absolute left-0 top-1 bottom-1 w-[2px] rounded-full transition-all duration-500 ease-in-out",
              activeIdeaIndex === 2 ? "bg-slate-600/60" : "bg-transparent"
            )} />
            <h2 className="text-[10px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-3.5">
              03 · Execution gating
            </h2>
            <p className="text-[14.5px] font-semibold text-slate-100 leading-snug mb-4 max-w-[560px] tracking-[-0.01em]">
              Stream completion is not sufficient to execute a tool. A state check is required.
            </p>
            <div className="text-[14px] leading-[1.88] text-slate-400 space-y-4 max-w-[580px]">
              <p>
                A streamed response may end for reasons other than a tool invocation — reaching{" "}
                <IC>max_tokens</IC>, a natural <IC>stop_sequence</IC>, or ordinary message completion.
                The spec requires verifying <IC>stop_reason === 'tool_use'</IC> before executing.{" "}
                {c("anthropic-docs-stop")} Without this check, the handler may attempt to
                call a tool that was never requested, or silently skip one that was. {c("so-stop-reason")}
              </p>
              <p>
                The SDK's <IC>contentBlock</IC> event handles this implicitly — it only fires
                for complete, confirmed tool use blocks. At the raw event level,
                this check is your responsibility.
              </p>
            </div>
          </article>

          <Divider />

          {/* ── Idea 4: Token budget ── */}
          <article
            className="relative mb-0 pl-5 scroll-mt-20"
            data-idea="budget"
          >
            <div className={cn(
              "absolute left-0 top-1 bottom-1 w-[2px] rounded-full transition-all duration-500 ease-in-out",
              activeIdeaIndex === 3 ? "bg-slate-600/60" : "bg-transparent"
            )} />
            <h2 className="text-[10px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-3.5">
              04 · Token budget
            </h2>
            <p className="text-[14.5px] font-semibold text-slate-100 leading-snug mb-4 max-w-[560px] tracking-[-0.01em]">
              A conservative token limit can truncate tool arguments mid-stream with no explicit error.
            </p>
            <div className="text-[14px] leading-[1.88] text-slate-400 space-y-4 max-w-[580px]">
              <p>
                If <IC>max_tokens</IC> is exhausted while the model is generating tool argument
                JSON, the stream terminates before <IC>content_block_stop</IC> fires. The API
                returns no explicit error — you receive malformed JSON and, depending on your
                error handling, may proceed silently with corrupted data. {c("forum-maxtokens")}
              </p>
              <p>
                Teams that use tools heavily set <IC>max_tokens</IC> to 4096 or higher,
                treating it as a budget independent of expected text output — because the model
                must also produce the full tool input JSON within that limit. {c("hn-39482103")}
              </p>
            </div>
          </article>

          <div className="h-28" />
        </div>
      </div>

      {/* ── Source map sidebar ── */}
      <aside className="w-[216px] shrink-0 border-l border-slate-800/30 hidden lg:flex flex-col pt-20 pb-8 px-5 bg-[#05060C]">
        <div className="sticky top-20 flex flex-col">

          {/* Concept navigator */}
          <div className="mb-7">
            <p className="text-[8.5px] font-mono tracking-[0.32em] text-slate-700 uppercase mb-4">
              Reading
            </p>
            <div className="space-y-1">
              {IDEAS.map((idea, i) => {
                const isActive = i === activeIdeaIndex;
                return (
                  <div
                    key={idea.id}
                    className={cn(
                      "flex items-start gap-2 py-1.5 pl-2 pr-1 rounded transition-all duration-300 ease-in-out",
                      isActive ? "bg-slate-800/30" : ""
                    )}
                  >
                    <span className={cn(
                      "text-[9px] font-mono mt-[2.5px] shrink-0 transition-colors duration-300",
                      isActive ? "text-slate-400" : "text-slate-700"
                    )}>
                      0{i + 1}
                    </span>
                    <span className={cn(
                      "text-[10.5px] leading-snug transition-colors duration-300",
                      isActive ? "text-slate-300" : "text-slate-700"
                    )}>
                      {idea.concept}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Source panel */}
          <div className="border-t border-slate-800/50 pt-5">
            {/* Panel header */}
            <div className="flex items-center justify-between mb-3.5">
              <p className="text-[8.5px] font-mono tracking-[0.32em] text-slate-700 uppercase">
                {hoveredSource ? "Inspecting" : `Sources · 0${activeIdeaIndex + 1}`}
              </p>
              {hoveredSource && (
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  TYPE_STYLE[hoveredSource.type].dot
                )} />
              )}
            </div>

            {/* Panel content — fades on change */}
            <div
              className="transition-opacity duration-100 ease-in-out"
              style={{ opacity: panelVisible ? 1 : 0 }}
            >
              {hoveredSource ? (
                /* Inspecting a specific citation */
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "text-[8.5px] font-mono uppercase tracking-wider",
                      TYPE_STYLE[hoveredSource.type].label
                    )}>
                      {TYPE_STYLE[hoveredSource.type].text}
                    </span>
                    <span className="text-[8.5px] font-mono text-slate-700">·</span>
                    <span className="text-[8.5px] font-mono text-slate-700">{hoveredSource.meta}</span>
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
                /* Concept source overview */
                <div>
                  <div className="space-y-3 mb-4">
                    {activeSources.map((src) => (
                      <div key={src.id} className="flex items-start gap-2">
                        <div className={cn(
                          "w-[5px] h-[5px] rounded-full shrink-0 mt-[4.5px]",
                          TYPE_STYLE[src.type].dot
                        )} />
                        <div>
                          <span className={cn(
                            "text-[8.5px] font-mono uppercase tracking-wide block mb-0.5",
                            TYPE_STYLE[src.type].label
                          )}>
                            {TYPE_STYLE[src.type].text}
                          </span>
                          <p className="text-[10.5px] text-slate-500 leading-snug">
                            {src.label}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Interaction hint */}
                  <p className="text-[8.5px] font-mono text-slate-700 leading-relaxed border-t border-slate-800/40 pt-3">
                    hover citations in the text to inspect any source
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Source composition footer */}
          <div className="border-t border-slate-800/40 mt-6 pt-5">
            <div className="flex justify-between items-center mb-3">
              <span className="text-[8.5px] font-mono tracking-[0.2em] text-slate-700 uppercase">
                Corpus
              </span>
              <span className="text-[11px] font-light text-slate-700 tabular-nums">
                {Object.keys(SOURCES).length} sources
              </span>
            </div>
            <div className="space-y-1.5">
              {(["docs", "practice", "failure"] as KnowledgeType[]).map((t) => {
                const count = Object.values(SOURCES).filter((s) => s.type === t).length;
                const total = Object.keys(SOURCES).length;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={t} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <div className={cn("w-[5px] h-[5px] rounded-full", TYPE_STYLE[t].dot)} />
                        <span className={cn(
                          "text-[8.5px] font-mono uppercase tracking-wide",
                          TYPE_STYLE[t].label
                        )}>
                          {TYPE_STYLE[t].text}
                        </span>
                      </div>
                      <span className="text-[9px] font-mono text-slate-700">{count}</span>
                    </div>
                    {/* Proportion bar */}
                    <div className="h-[2px] rounded-full bg-slate-800/60 overflow-hidden">
                      <div
                        className={cn("h-full rounded-full opacity-50", TYPE_STYLE[t].dot)}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </aside>

    </div>
  );
}
