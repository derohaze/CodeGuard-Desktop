import { ReactNode } from "react";
import { motion } from "framer-motion";

interface SectionShellProps {
  children: ReactNode;
  className?: string;
  dark?: boolean;
  dotted?: boolean;
  id?: string;
}

export function SectionShell({ children, className = "", dark, dotted, id }: SectionShellProps) {
  return (
    <section id={id} className={`relative py-20 md:py-28 ${dark ? "section-dark" : ""} ${className}`}>
      {dotted && !dark && <div className="absolute inset-0 dotted-grid opacity-25 pointer-events-none" />}
      {dotted && dark && <div className="absolute inset-0 dotted-grid-dark opacity-30 pointer-events-none" />}
      <div className="relative max-w-content mx-auto px-6">{children}</div>
    </section>
  );
}

export function SectionHeader({ overline, title, subtitle, center, dark }: {
  overline?: string;
  title: ReactNode;
  subtitle?: string;
  center?: boolean;
  dark?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5 }}
      className={`mb-14 ${center ? "text-center max-w-2xl mx-auto" : "max-w-2xl"}`}
    >
      {overline && <span className="mono-label text-text-tertiary mb-3 block">{overline}</span>}
      <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">{title}</h2>
      {subtitle && <p className={`text-base leading-relaxed ${dark ? "text-dark-muted" : "text-text-secondary"}`}>{subtitle}</p>}
    </motion.div>
  );
}
