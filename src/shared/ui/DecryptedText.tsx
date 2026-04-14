import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

interface DecryptedTextProps {
  text: string;
  speed?: number;
  className?: string;
  encryptedClassName?: string;
  parentClassName?: string;
  characters?: string;
}

export function DecryptedText({
  text,
  speed = 26,
  className = "",
  encryptedClassName = "",
  parentClassName = "",
  characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState(text);
  const [revealedCount, setRevealedCount] = useState(0);
  const intervalRef = useRef<number | null>(null);

  const availableChars = useMemo(() => characters.split(""), [characters]);

  useEffect(() => {
    setRevealedCount(0);

    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
    }

    const nextFrame = () =>
      text
        .split("")
        .map((char, index) => {
          if (char === " ") return " ";
          if (index < revealedCount) return char;
          return availableChars[Math.floor(Math.random() * availableChars.length)] ?? char;
        })
        .join("");

    setDisplayText(nextFrame());

    intervalRef.current = window.setInterval(() => {
      setRevealedCount((current) => {
        const next = current + 1;
        if (next >= text.length) {
          if (intervalRef.current !== null) {
            window.clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setDisplayText(text);
          return text.length;
        }
        return next;
      });
    }, speed);

    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [availableChars, speed, text]);

  useEffect(() => {
    if (revealedCount >= text.length) {
      setDisplayText(text);
      return;
    }

    setDisplayText(
      text
        .split("")
        .map((char, index) => {
          if (char === " ") return " ";
          if (index < revealedCount) return char;
          return availableChars[Math.floor(Math.random() * availableChars.length)] ?? char;
        })
        .join(""),
    );
  }, [availableChars, revealedCount, text]);

  return (
    <motion.span
      initial={{ opacity: 0.82 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={`inline-block whitespace-pre ${parentClassName}`}
      aria-label={text}
    >
      {displayText.split("").map((char, index) => {
        const isRevealed = index < revealedCount || revealedCount >= text.length;
        return (
          <span key={`${text}-${index}`} className={isRevealed ? className : encryptedClassName}>
            {char}
          </span>
        );
      })}
    </motion.span>
  );
}
