import * as React from "react";
import { cn } from "@/lib/utils";

export function Label({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="field-label"
      className={cn("text-sm font-medium text-txt-primary", className)}
      {...props}
    />
  );
}

export function Description({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      slot="description"
      className={cn("text-sm leading-6 text-txt-secondary", className)}
      {...props}
    />
  );
}
