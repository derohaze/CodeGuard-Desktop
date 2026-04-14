import * as React from "react";
import { cn } from "@/lib/utils";

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;

interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel;
}

const levelClassNames: Record<HeadingLevel, string> = {
  1: "text-3xl font-semibold tracking-[-0.04em] md:text-[2rem]",
  2: "text-2xl font-semibold tracking-[-0.035em] md:text-[1.7rem]",
  3: "text-xl font-semibold tracking-[-0.03em] md:text-[1.35rem]",
  4: "text-lg font-semibold tracking-[-0.025em]",
  5: "text-base font-semibold tracking-[-0.02em]",
  6: "text-sm font-semibold tracking-[-0.015em] uppercase",
};

export function Heading({ level = 2, className, children, ...props }: HeadingProps) {
  const Comp = `h${level}` as const;

  return (
    <Comp
      className={cn("text-balance text-txt-primary", levelClassNames[level], className)}
      {...props}
    >
      {children}
    </Comp>
  );
}
