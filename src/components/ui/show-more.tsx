import * as React from "react";
import { cn } from "@/lib/utils";

interface ShowMoreRenderProps {
  isSelected: boolean;
}

interface ShowMoreProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  children: (props: ShowMoreRenderProps) => React.ReactNode;
}

export function ShowMore({ children, className, onClick, ...props }: ShowMoreProps) {
  const [isSelected, setIsSelected] = React.useState(false);

  return (
    <div className={cn("my-2 flex items-center self-stretch", className)}>
      <div className="me-2 h-px flex-1 border-t border-border-soft" />
      <button
        type="button"
        onClick={(event) => {
          setIsSelected((current) => !current);
          onClick?.(event);
        }}
        className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1.5 text-sm text-txt-primary"
        style={{ borderColor: "hsl(var(--border-soft))" }}
        {...props}
      >
        {children({ isSelected })}
      </button>
      <div className="ms-2 h-px flex-1 border-t border-border-soft" />
    </div>
  );
}
