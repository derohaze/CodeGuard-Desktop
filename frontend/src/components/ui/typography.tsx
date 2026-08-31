import * as React from "react";
import { cn } from "@/lib/utils";

export function Typography({
  className,
  ...props
}: React.ComponentPropsWithoutRef<"div">) {
  return (
    <div
      className={cn(
        "max-w-none text-[15px] leading-8 text-txt-primary [overflow-wrap:anywhere] [&_a]:font-medium [&_a]:text-[#8a5a24] [&_a]:underline-offset-4 hover:[&_a]:underline [&_blockquote]:border-s-2 [&_blockquote]:border-border-soft [&_blockquote]:ps-4 [&_blockquote]:italic [&_code]:rounded-md [&_code]:bg-[#efe8de] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.92em] [&_em]:italic [&_strong]:font-semibold",
        className,
      )}
      {...props}
    />
  );
}
