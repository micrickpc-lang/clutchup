export const spring = {
  fast: { type: "spring", stiffness: 420, damping: 34, mass: 0.75 },
  panel: { type: "spring", stiffness: 260, damping: 28, mass: 0.9 },
  soft: { type: "spring", stiffness: 180, damping: 24, mass: 1 },
} as const;

export const timing = { page: 0.28, game: 0.55, found: 0.82 } as const;
