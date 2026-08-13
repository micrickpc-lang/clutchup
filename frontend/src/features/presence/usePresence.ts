import { useEffect } from "react";
import { endpoints } from "../../api/client";

export function usePresence(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    let timer: number | undefined;
    const beat = () => {
      if (document.visibilityState === "visible") void endpoints.heartbeat().catch(() => undefined);
      window.clearTimeout(timer);
      timer = window.setTimeout(beat, document.visibilityState === "visible" ? 35_000 : 90_000);
    };
    const visibility = () => beat();
    beat();
    document.addEventListener("visibilitychange", visibility);
    return () => { window.clearTimeout(timer); document.removeEventListener("visibilitychange", visibility); };
  }, [enabled]);
}
