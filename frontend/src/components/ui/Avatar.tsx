import { useState } from "react";
import { UserRound } from "lucide-react";

export function Avatar({ src, name, size = "md", lazy = true }: { src: string | null; name: string; size?: "sm" | "md" | "lg" | "xl"; lazy?: boolean }) {
  const [failed, setFailed] = useState(false);
  const sizes = { sm: "avatar-sm", md: "avatar-md", lg: "avatar-lg", xl: "avatar-xl" };
  if (!src || failed) return <div className={`avatar ${sizes[size]} avatar-fallback`} role="img" aria-label={`Аватар ${name}`}><UserRound aria-hidden /></div>;
  return <img src={src} alt={`Аватар ${name}`} loading={lazy ? "lazy" : "eager"} onError={() => setFailed(true)} className={`avatar ${sizes[size]}`} />;
}
