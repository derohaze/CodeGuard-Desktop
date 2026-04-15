import { BuilderStructuredMessage } from "./message-renderer/BuilderStructuredMessage";

export function BuilderMessageText({
  text,
  isStreaming,
  tone = "default",
}: {
  text: string;
  isStreaming: boolean;
  tone?: "default" | "inverted";
}) {
  return <BuilderStructuredMessage text={text} isStreaming={isStreaming} tone={tone} />;
}
