import { Link2, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { endpoints, errorMessage } from "../../api/client";
import { openExternal } from "../../lib/telegram";
import type { Profile } from "../../types/api";

type State = "idle" | "opening" | "checking" | "connected";

export function ConnectFaceit({ onConnected, error }: { onConnected: (profile: Profile) => void; error: (text: string) => void }) {
  const [state, setState] = useState<State>("idle");
  const timer = useRef<number>();
  const attempts = useRef(0);
  const active = useRef(true);
  const stateRef = useRef<State>("idle");

  useEffect(() => { stateRef.current = state; }, [state]);

  const stop = useCallback(() => {
    window.clearInterval(timer.current);
    attempts.current = 0;
  }, []);

  const check = useCallback(async (): Promise<boolean> => {
    try {
      const profile = await endpoints.profile();
      if (profile && active.current) {
        stop();
        setState("connected");
        onConnected(profile);
        return true;
      }
    } catch {
      // A transient profile request must not create another OAuth session.
    }
    return false;
  }, [onConnected, stop]);

  const startPolling = useCallback(() => {
    window.clearInterval(timer.current);
    timer.current = window.setInterval(async () => {
      if (!active.current || await check()) return;
      attempts.current += 1;
      if (attempts.current >= 30) {
        stop();
        setState("idle");
        error("Не удалось подтвердить подключение FACEIT. Вернитесь в приложение и попробуйте ещё раз.");
      }
    }, 2_000);
  }, [check, error, stop]);

  useEffect(() => {
    active.current = true;
    const message = (event: MessageEvent) => {
      if (event.origin === window.location.origin && event.data?.type === "clutchup-faceit-connected") void check();
    };
    const returned = () => {
      if (document.visibilityState === "visible" && stateRef.current === "checking") void check();
    };
    window.addEventListener("message", message);
    window.addEventListener("focus", returned);
    document.addEventListener("visibilitychange", returned);
    return () => {
      active.current = false;
      stop();
      window.removeEventListener("message", message);
      window.removeEventListener("focus", returned);
      document.removeEventListener("visibilitychange", returned);
    };
  }, [check, stop]);

  async function connect() {
    if (state !== "idle") return;
    setState("opening");
    try {
      const result = await endpoints.oauthStart();
      openExternal(result.authorization_url);
      if (!active.current) return;
      setState("checking");
      attempts.current = 0;
      startPolling();
    } catch (cause) {
      if (!active.current) return;
      setState("idle");
      error(errorMessage(cause));
    }
  }

  const label = state === "opening" ? "Открываем FACEIT…" : state === "checking" ? "Проверяем подключение…" : state === "connected" ? "FACEIT подключён" : "Войти через FACEIT";
  return <section className="connect-page"><div className="faceit-logo">F</div><h1>Подключите FACEIT</h1><p>Войдите через официальный сайт FACEIT. Никнейм, аватар, ELO и доступная статистика загрузятся автоматически.</p><button className="button faceit" disabled={state !== "idle"} onClick={connect}><Link2 />{label}</button><small><ShieldCheck />Пароль остаётся на accounts.faceit.com</small></section>;
}
