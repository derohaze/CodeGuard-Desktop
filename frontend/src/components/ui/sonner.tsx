import { useTheme } from "next-themes";
import { Toaster as Sonner, toast } from "sonner";
import { CheckCircle2, CircleAlert, Info, LoaderCircle, TriangleAlert } from "lucide-react";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      position="top-center"
      closeButton
      expand={false}
      visibleToasts={4}
      gap={8}
      className="toaster group"
      icons={{
        success: <CheckCircle2 className="size-3.5 text-emerald-500" strokeWidth={2} />,
        error: <CircleAlert className="size-3.5 text-rose-500" strokeWidth={2} />,
        warning: <TriangleAlert className="size-3.5 text-amber-500" strokeWidth={2} />,
        info: <Info className="size-3.5 text-sky-400" strokeWidth={2} />,
        loading: <LoaderCircle className="size-3.5 animate-spin text-white/60" strokeWidth={2} />,
      }}
      toastOptions={{
        classNames: {
          toast:
            "group toast !w-[360px] !max-w-[90vw] relative flex items-center gap-2.5 rounded-[10px] border border-white/[0.08] !bg-[#262626] px-3 py-2 pr-9 shadow-[0_12px_32px_rgba(0,0,0,0.55)] !backdrop-blur-none",
          actionButton: "group-[.toast]:bg-white group-[.toast]:text-black text-[12px] h-7 rounded-md px-3",
          cancelButton: "group-[.toast]:bg-white/10 group-[.toast]:text-white/70 text-[12px] h-7 rounded-md px-3",
          title: "!text-[12.5px] !font-medium !leading-none !text-white !tracking-[-0.01em]",
          description: "!text-[12px] !leading-4 !text-white/60",
          icon: "!mr-0 shrink-0",
          closeButton:
            "!absolute !left-auto !right-1.5 !top-1/2 !-translate-y-1/2 !bg-transparent !border-0 !shadow-none !text-white/40 hover:!text-white hover:!bg-white/[0.06] !rounded-md !h-6 !w-6 !p-0 !m-0",
        },
        duration: 4000,
      }}
      style={
        {
          "--normal-bg": "#262626",
          "--normal-border": "rgba(255,255,255,0.08)",
          "--normal-text": "#fff",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster, toast };
