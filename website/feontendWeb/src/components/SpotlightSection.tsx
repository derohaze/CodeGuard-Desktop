import { motion } from "framer-motion";
import { ReactNode } from "react";

interface SpotlightSectionProps {
  overline?: string;
  title: string;
  description: string;
  visual: ReactNode;
  reversed?: boolean;
  dark?: boolean;
}

export function SpotlightSection({ overline, title, description, visual, reversed, dark }: SpotlightSectionProps) {
  return (
    <section className={`py-20 md:py-28 ${dark ? "section-dark" : ""}`}>
      <div className={`max-w-content mx-auto px-6 flex flex-col ${reversed ? "lg:flex-row-reverse" : "lg:flex-row"} items-center gap-12 lg:gap-20`}>
        <motion.div
          initial={{ opacity: 0, x: reversed ? 20 : -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="flex-1 max-w-lg"
        >
          {overline && <span className="mono-label text-text-tertiary mb-3 block">{overline}</span>}
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">{title}</h2>
          <p className={`text-base leading-relaxed ${dark ? "text-dark-muted" : "text-text-secondary"}`}>{description}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, x: reversed ? -20 : 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="flex-1 w-full"
        >
          {visual}
        </motion.div>
      </div>
    </section>
  );
}
