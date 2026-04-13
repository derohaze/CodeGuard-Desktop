import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface WorkflowStepProps {
  step: number;
  title: string;
  description: string;
  icon: LucideIcon;
  isLast?: boolean;
}

export function WorkflowStep({ step, title, description, icon: Icon, isLast }: WorkflowStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: step * 0.08 }}
      className="relative flex gap-5"
    >
      <div className="flex flex-col items-center">
        <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold shrink-0">
          {step}
        </div>
        {!isLast && <div className="w-px flex-1 bg-border mt-2" />}
      </div>
      <div className={`pb-12 ${isLast ? "pb-0" : ""}`}>
        <div className="flex items-center gap-2 mb-2">
          <Icon className="w-4 h-4 text-text-secondary" />
          <h3 className="font-semibold text-foreground">{title}</h3>
        </div>
        <p className="text-sm text-text-secondary leading-relaxed max-w-md">{description}</p>
      </div>
    </motion.div>
  );
}
