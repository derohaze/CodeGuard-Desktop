import * as React from "react";
import { cn } from "@/lib/utils";

const DescriptionList = React.forwardRef<HTMLDListElement, React.ComponentPropsWithoutRef<"dl">>(
  ({ className, ...props }, ref) => (
    <dl
      ref={ref}
      className={cn(
        "grid grid-cols-1 gap-x-5 text-[15px] leading-7 sm:grid-cols-[minmax(160px,240px)_1fr]",
        className,
      )}
      {...props}
    />
  ),
);
DescriptionList.displayName = "DescriptionList";

const DescriptionTerm = React.forwardRef<HTMLElement, React.ComponentPropsWithoutRef<"dt">>(
  ({ className, ...props }, ref) => (
    <dt
      ref={ref}
      className={cn(
        "border-t border-border-soft pt-3 font-medium text-txt-secondary first:border-none sm:py-3",
        className,
      )}
      {...props}
    />
  ),
);
DescriptionTerm.displayName = "DescriptionTerm";

const DescriptionDetails = React.forwardRef<HTMLElement, React.ComponentPropsWithoutRef<"dd">>(
  ({ className, ...props }, ref) => (
    <dd
      ref={ref}
      className={cn(
        "border-t border-border-soft pb-3 pt-1 text-txt-primary first:border-none sm:py-3",
        className,
      )}
      {...props}
    />
  ),
);
DescriptionDetails.displayName = "DescriptionDetails";

export { DescriptionDetails, DescriptionList, DescriptionTerm };
