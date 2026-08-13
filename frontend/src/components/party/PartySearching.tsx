import { motion, useReducedMotion } from "motion/react";
import styles from "./PartySearching.module.css";

export function PartySearching() {
  const reduced = useReducedMotion();

  return (
    <div className={styles.root} role="status" aria-live="polite">
      <div className={styles.radar} aria-hidden="true">
        <motion.span
          className={styles.sweep}
          animate={reduced ? undefined : { rotate: 360 }}
          transition={{ duration: 2.4, ease: "linear", repeat: Infinity }}
        />
        <span className={styles.dot} />
      </div>
      <div>
        <strong>SEARCHING FOR PLAYERS</strong>
        <p>Scanning open parties for your filters.</p>
      </div>
    </div>
  );
}
