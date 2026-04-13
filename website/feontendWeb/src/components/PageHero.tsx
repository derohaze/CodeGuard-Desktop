import { motion } from "framer-motion";
import { ReactNode } from "react";

interface PageHeroProps {
  overline?: string;
  title: ReactNode;
  subtitle: string;
  children?: ReactNode;
  dark?: boolean;
}

export function PageHero({ overline, title, subtitle, children, dark }: PageHeroProps) {
  return (
    <section className={`relative py-24 md:py-32 overflow-hidden ${dark ? "section-dark" : ""}`}>
      {!dark && <div className="absolute inset-0 dotted-grid opacity-30" />}
      {dark && <div className="absolute inset-0 dotted-grid-dark opacity-40" />}
      <div className="relative max-w-content mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          {overline && (
            <span className="mono-label text-text-tertiary mb-4 block">
              {overline}
            </span>
          )}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] mb-6">
            {title}
          </h1>
          <p className={`text-lg md:text-xl leading-relaxed max-w-2xl ${dark ? "text-dark-muted" : "text-text-secondary"}`}>
            {subtitle}
          </p>
          {children && <div className="mt-8 flex flex-wrap gap-4">{children}</div>}
        </motion.div>
      </div>
    </section>
  );
}
