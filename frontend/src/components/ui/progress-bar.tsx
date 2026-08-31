import * as React from "react";
import { twMerge } from "tailwind-merge";
import { cn } from "@/lib/utils";

interface ProgressBarContextValue {
  percentage: number;
  valueText: string;
}

const ProgressBarContext = React.createContext<ProgressBarContextValue | null>(null);

interface ProgressBarProps extends React.ComponentProps<"div"> {
  value: number;
}

export function ProgressBar({ className, value, children, ...props }: ProgressBarProps) {
  const percentage = Math.max(0, Math.min(100, value));

  return (
    <ProgressBarContext.Provider value={{ percentage, valueText: `${percentage}%` }}>
      <div
        data-slot="control"
        className={cn(
          "w-full",
          "[&>[data-slot=progress-bar-header]+[data-slot=progress-bar-track]]:mt-2",
          "[&>[data-slot=progress-bar-header]+[slot='description']]:mt-1",
          "[&>[slot='description']+[data-slot=progress-bar-track]]:mt-2",
          "[&>[data-slot=progress-bar-track]+[slot=description]]:mt-2",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    </ProgressBarContext.Provider>
  );
}

export function ProgressBarHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="progress-bar-header"
      className={twMerge("flex items-center justify-between", className)}
      {...props}
    />
  );
}

export function ProgressBarValue({
  className,
  ...props
}: Omit<React.ComponentProps<"span">, "children">) {
  const context = React.useContext(ProgressBarContext);

  if (!context) return null;

  return (
    <span
      data-slot="progress-bar-value"
      className={twMerge("text-sm tabular-nums text-txt-tertiary", className)}
      {...props}
    >
      {context.valueText}
    </span>
  );
}

export function ProgressBarTrack({ className, ...props }: React.ComponentProps<"div">) {
  const context = React.useContext(ProgressBarContext);

  if (!context) return null;

  return (
    <span data-slot="progress-bar-track" className="relative block w-full">
      <div className="flex w-full items-center gap-x-2" {...props}>
        <div
          data-slot="progress-container"
          className={twMerge(
            "[--progress-content-bg:hsl(var(--primary))] relative h-1.5 w-full overflow-hidden rounded-full bg-[#ece3d6]",
            className,
          )}
        >
          <div
            data-slot="progress-content"
            className="absolute left-0 top-0 h-full rounded-full bg-[var(--progress-content-bg)] transition-[width] duration-200 ease-linear"
            style={{ width: `${context.percentage}%` }}
          />
        </div>
      </div>
    </span>
  );
}
