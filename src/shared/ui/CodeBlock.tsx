interface CodeLineAnnotation {
  lineStart: number;
  lineEnd: number;
  tone: "red" | "yellow";
}

interface CodeBlockProps {
  code: string;
  annotations?: CodeLineAnnotation[];
}

export function CodeBlock({ code, annotations = [] }: CodeBlockProps) {
  const parsedLines = code.split("\n").map((rawLine) => {
    const match = rawLine.match(/^(\d+):\s?(.*)$/);
    if (!match) {
      return { number: null, content: rawLine };
    }
    return {
      number: Number(match[1]),
      content: match[2],
    };
  });

  return (
    <div className="overflow-x-auto rounded-xl border bg-surface-code p-3" style={{ borderColor: "hsl(var(--border-soft))" }}>
      <div className="min-w-full font-mono text-[13px] leading-relaxed text-txt-primary">
        {parsedLines.map((line, index) => {
          const tone = resolveLineTone(line.number, annotations);
          const toneClass =
            tone === "red"
              ? "bg-[#fff1ee]"
              : tone === "yellow"
                ? "bg-[#fbf6e8]"
                : "";

          return (
            <div
              key={`${line.number ?? "plain"}-${index}`}
              className={`grid grid-cols-[56px_minmax(0,1fr)] gap-3 rounded-md px-2 py-0.5 ${toneClass}`}
            >
              <span className="select-none text-right text-xs text-txt-tertiary">
                {line.number ?? ""}
              </span>
              <pre className="whitespace-pre-wrap break-words">{line.content}</pre>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function resolveLineTone(lineNumber: number | null, annotations: CodeLineAnnotation[]) {
  if (lineNumber === null) {
    return null;
  }
  for (const annotation of annotations) {
    if (lineNumber >= annotation.lineStart && lineNumber <= annotation.lineEnd) {
      return annotation.tone;
    }
  }
  return null;
}
