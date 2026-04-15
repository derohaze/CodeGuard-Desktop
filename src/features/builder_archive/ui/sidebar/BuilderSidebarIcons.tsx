export function SidebarFolderIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className={className}>
      <path
        d="M1.75 5.25C1.75 4.42157 2.42157 3.75 3.25 3.75H5.06434C5.3668 3.75 5.65411 3.88698 5.84388 4.12272L6.28112 4.66578C6.47089 4.90152 6.7582 5.0385 7.06066 5.0385H12.75C13.5784 5.0385 14.25 5.71007 14.25 6.5385V10.75C14.25 11.5784 13.5784 12.25 12.75 12.25H3.25C2.42157 12.25 1.75 11.5784 1.75 10.75V5.25Z"
        stroke="currentColor"
        strokeWidth="1.45"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CollapseAllIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="h-[15px] w-[15px]">
      <path d="M3.25 5.5H12.75" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
      <path d="M3.25 8H12.75" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
      <path d="M3.25 10.5H8.75" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
    </svg>
  );
}

export function ReopenPreviousIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="h-[15px] w-[15px]">
      <path d="M6 3.5 2.75 6.75 6 10" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3.25 6.75H8.25C10.7353 6.75 12.75 8.76472 12.75 11.25V12.5" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ExpandAllIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="h-[15px] w-[15px]">
      <path d="M4.25 3.75H11.75V11.25H4.25V3.75Z" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 6V9.75" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
      <path d="M6.125 7.875H9.875" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
    </svg>
  );
}
