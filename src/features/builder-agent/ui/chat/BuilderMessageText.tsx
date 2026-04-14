export function BuilderMessageText({ text, isStreaming }: { text: string; isStreaming: boolean }) {
  return (
    <p
      dir="auto"
      className="whitespace-pre-wrap break-words text-start"
      style={{ unicodeBidi: "plaintext" }}
    >
      {text}
      {isStreaming && <span className="ml-0.5 inline-block h-5 w-[2px] animate-pulse align-[-2px] bg-current opacity-45" />}
    </p>
  );
}
