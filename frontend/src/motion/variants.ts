import type { Variants } from "motion/react";
import { spring } from "./tokens";

export const pageVariants: Variants = {
  initial: { opacity: 0, scale: 0.99, y: 10, z: -30 },
  enter: { opacity: 1, scale: 1, y: 0, z: 0, transition: spring.panel },
  exit: { opacity: 0, scale: 0.985, y: -4, z: -30, transition: { duration: 0.2 } },
};
export const cardVariants: Variants = {
  initial: { opacity: 0, y: 18, rotateX: 2, scale: 0.985 },
  enter: (index: number) => ({ opacity: 1, y: 0, rotateX: 0, scale: 1, transition: { ...spring.panel, delay: index * 0.055 } }),
  exit: { opacity: 0, scale: 0.97, z: -60, filter: "blur(4px)", transition: { duration: 0.2 } },
};
