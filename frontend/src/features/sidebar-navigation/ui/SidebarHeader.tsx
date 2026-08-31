import { BrandModeHeading } from "@/shared/ui/BrandModeHeading";

export function SidebarHeader() {
  return (
    <div className="px-4 pb-2 pt-4">
      <div className="flex items-center gap-2">
        <BrandModeHeading />
      </div>
      <p className="mt-1 text-[11px] font-medium tracking-wide text-txt-tertiary/80">Security workspace</p>
    </div>
  );
}
