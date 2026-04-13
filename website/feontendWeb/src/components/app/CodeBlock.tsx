interface CodeBlockProps {
  code: string;
}

export function CodeBlock({ code }: CodeBlockProps) {
  return (
    <div className="rounded-xl bg-surface-code border border-border-soft p-4 overflow-x-auto">
      <pre className="font-mono text-[13px] leading-relaxed text-foreground whitespace-pre">{code}</pre>
    </div>
  );
}
