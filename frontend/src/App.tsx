import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import axios from "axios";
import {
  init,
  miniApp,
  openLink,
  swipeBehavior,
  themeParams,
  viewport,
} from "@telegram-apps/sdk";
import { api, type PlayerCardData, type Profile } from "./api/client";
import SwipeCard from "./components/SwipeCard";
type Tab = "search" | "matches" | "profile" | "settings";
const roles = ["Rifler", "AWPer", "IGL", "Support", "Lurker", "Entry"] as const;
export default function App() {
  const [tab, setTab] = useState<Tab>("search");
  const [profile, setProfile] = useState<Profile | null | undefined>();
  const [card, setCard] = useState<PlayerCardData | null>(null);
  const [matches, setMatches] = useState<PlayerCardData[]>([]);
  const [selected, setSelected] = useState<PlayerCardData | null>(null);
  const [matched, setMatched] = useState<PlayerCardData | null>(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    try {
      init();
      if (miniApp.mount.isAvailable()) miniApp.mount();
      if (themeParams.mount.isAvailable()) themeParams.mount();
      if (viewport.mount.isAvailable())
        void viewport.mount().then(() => viewport.expand());
      if (swipeBehavior.mount.isAvailable()) {
        swipeBehavior.mount();
        swipeBehavior.disableVertical();
      }
    } catch {}
    void load();
  }, []);
  async function load() {
    try {
      const r = await api.get<Profile | null>("/profile/me");
      setProfile(r.data);
      if (r.data) await Promise.all([loadCard(), loadMatches()]);
    } catch (e) {
      setError(messageOf(e));
      setProfile(null);
    }
  }
  async function loadCard() {
    setCard((await api.get<PlayerCardData | null>("/cards/next")).data);
  }
  async function loadMatches() {
    setMatches((await api.get<PlayerCardData[]>("/matches")).data);
  }
  async function swipe(direction: "like" | "dislike") {
    if (!card || busy) return;
    setBusy(true);
    try {
      const current = card;
      const r = await api.post<{ matched: boolean }>("/swipe", {
        target_user_id: card.user_id,
        direction,
      });
      if (r.data.matched) {
        setMatched(current);
        void loadMatches();
      }
      await loadCard();
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setBusy(false);
    }
  }
  if (profile === undefined)
    return (
      <Shell>
        <Center text="Загрузка…" />
      </Shell>
    );
  if (!profile || editing)
    return (
      <Shell>
        <ProfileForm
          initial={profile ?? undefined}
          onSaved={(p) => {
            setProfile(p);
            setEditing(false);
            setTab("search");
            void loadCard();
          }}
          setError={setError}
        />
        {error && <Toast text={error} close={() => setError("")} />}
      </Shell>
    );
  if (matched)
    return (
      <MatchScreen
        first={profile}
        second={matched}
        close={() => setMatched(null)}
      />
    );
  if (selected)
    return <PlayerDetails player={selected} close={() => setSelected(null)} />;
  return (
    <Shell>
      <Header tab={tab} />
      {error && <Toast text={error} close={() => setError("")} />}
      <div className="flex-1 overflow-y-auto px-4 pb-24">
        {tab === "search" &&
          (card ? (
            <SwipeCard
              player={card}
              busy={busy}
              onSwipe={swipe}
              onInfo={() => setSelected(card)}
            />
          ) : (
            <Center text="Подходящих игроков пока нет" />
          ))}
        {tab === "matches" && <Matches items={matches} select={setSelected} />}{" "}
        {tab === "profile" && (
          <ProfileView profile={profile} edit={() => setEditing(true)} />
        )}{" "}
        {tab === "settings" && <Settings />}
      </div>
      <BottomNav
        tab={tab}
        setTab={(t) => {
          setTab(t);
          if (t === "matches") void loadMatches();
        }}
      />
    </Shell>
  );
}
function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="relative flex h-[100dvh] min-h-0 w-full flex-col overflow-hidden bg-[radial-gradient(circle_at_top,#111b2d_0,#050b13_48%)] text-white">
      {children}
    </main>
  );
}
function Header({ tab }: { tab: Tab }) {
  const title =
    tab === "search"
      ? "Find Teammates"
      : tab === "matches"
        ? "Матчи"
        : tab === "profile"
          ? "Профиль"
          : "Настройки";
  return (
    <header className="flex h-20 shrink-0 items-center justify-center px-4">
      <div className="absolute left-5 text-3xl text-violet-500">♦</div>
      <div className="text-center">
        <h1 className="text-xl font-bold">{title}</h1>
        {tab === "search" && <p className="text-xs text-slate-500">CS2</p>}
      </div>
    </header>
  );
}
function BottomNav({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const tabs: [Tab, string, string][] = [
    ["search", "⌕", "Поиск"],
    ["matches", "▣", "Матчи"],
    ["profile", "♙", "Профиль"],
    ["settings", "⚙", "Настройки"],
  ];
  return (
    <nav className="absolute inset-x-0 bottom-0 grid h-20 grid-cols-4 border-t border-white/10 bg-[#07101c]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      {tabs.map(([id, icon, label]) => (
        <button
          key={id}
          onClick={() => setTab(id)}
          className={`flex flex-col items-center justify-center gap-1 text-xs ${tab === id ? "text-violet-400" : "text-slate-500"}`}
        >
          <span className="text-2xl">{icon}</span>
          {label}
        </button>
      ))}
    </nav>
  );
}
function Matches({
  items,
  select,
}: {
  items: PlayerCardData[];
  select: (p: PlayerCardData) => void;
}) {
  return (
    <div>
      <div className="mb-4 grid grid-cols-3 rounded-xl bg-[#111a28] p-1 text-xs">
        <button className="rounded-lg bg-violet-900/60 py-2 text-violet-300">
          Все
        </button>
        <button>Новые</button>
        <button>Онлайн</button>
      </div>
      <div className="space-y-2">
        {items.length ? (
          items.map((p) => (
            <button
              key={p.user_id}
              onClick={() => select(p)}
              className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-[#0d1724] p-3 text-left"
            >
              <Avatar src={p.avatar_url} name={p.faceit_nickname} />
              <div className="min-w-0 flex-1">
                <p className="font-bold">
                  {p.faceit_nickname} <b className="text-violet-400">◆</b>
                </p>
                <p className="text-xs text-slate-500">
                  @{p.telegram_username ?? "player"}
                </p>
                <p className="mt-1 text-[10px] text-green-400">● Онлайн</p>
              </div>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-violet-600">
                •••
              </span>
            </button>
          ))
        ) : (
          <Center text="Мэтчей пока нет" />
        )}
      </div>
    </div>
  );
}
function ProfileView({
  profile,
  edit,
}: {
  profile: Profile;
  edit: () => void;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#0d1724] p-4">
      <div className="flex items-center gap-4">
        <Avatar src={profile.avatar_url} name={profile.faceit_nickname} big />
        <div>
          <h2 className="text-xl font-bold">
            {profile.faceit_nickname} <b className="text-violet-400">◆</b>
          </h2>
          <p className="text-sm text-slate-500">
            FACEIT level {profile.skill_level}
          </p>
          <p className="text-xs text-green-400">● Онлайн</p>
        </div>
      </div>
      <p className="mt-5 text-xs text-slate-500">О себе</p>
      <p className="mt-2 text-sm text-slate-300">
        {profile.bio || "Ищу сильную команду для совместной игры."}
      </p>
      <Stats
        elo={profile.elo}
        kd={profile.kd_ratio}
        level={profile.skill_level}
      />
      <div className="mt-3 grid grid-cols-2 rounded-xl border border-white/10 p-3">
        <Small label="Роль" value={profile.role} />
        <Small label="Стиль игры" value="Командный" />
      </div>
      <button
        onClick={edit}
        className="mt-5 w-full rounded-lg bg-slate-600 py-3 font-semibold"
      >
        Редактировать профиль
      </button>
    </div>
  );
}
function Settings() {
  const faceit = useFaceitConnect();
  return (
    <div className="space-y-3">
      <Panel>
        <Row a="Поиск игроков" b="ELO диапазон  ±250" />
        <Row a="Показывать только онлайн" b="●" purple />
      </Panel>
      <Panel>
        <Row a="Уведомления" b="Включены  ›" />
        <Row a="Язык приложения" b="Русский  ›" />
      </Panel>
      <Panel>
        <Row a="Telegram" b="Открыть в Telegram  ›" />
      </Panel>
      <button
        disabled={!faceit.ready}
        onClick={faceit.open}
        className="w-full rounded-xl border border-[#ff5500]/50 bg-[#ff5500]/10 py-4 font-bold text-[#ff7733] disabled:opacity-50"
      >
        {faceit.ready ? "Подключить FACEIT аккаунт" : "Подготавливаем FACEIT…"}
      </button>
      <Panel>
        <Row a="О приложении" b="ClutchUp v1.1.0" />
      </Panel>
    </div>
  );
}
function PlayerDetails({
  player,
  close,
}: {
  player: PlayerCardData;
  close: () => void;
}) {
  return (
    <Shell>
      <button onClick={close} className="absolute left-4 top-5 z-10 text-3xl">
        ‹
      </button>
      <div className="relative h-64">
        {player.avatar_url && (
          <img
            src={player.avatar_url}
            className="h-full w-full object-cover opacity-60"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#050b13] to-transparent" />
        <div className="absolute bottom-4 left-4 flex items-end gap-3">
          <Avatar src={player.avatar_url} name={player.faceit_nickname} big />
          <div>
            <h2 className="text-2xl font-bold">{player.faceit_nickname}</h2>
            <p className="text-sm text-slate-400">
              @{player.telegram_username ?? "player"}　
              <span className="text-green-400">● Онлайн</span>
            </p>
          </div>
        </div>
      </div>
      <div className="space-y-3 p-4">
        <Stats
          elo={player.elo}
          kd={player.kd_ratio}
          level={player.skill_level}
        />
        <Panel>
          <Small label="Роль" value={player.role} />
          <Small label="Стиль игры" value="Командный" />
        </Panel>
        <Panel>
          <p className="text-xs text-slate-500">О себе</p>
          <p className="mt-2 text-sm">
            {player.bio || "Люблю играть в команде и побеждать."}
          </p>
        </Panel>
        {player.telegram_username && (
          <a
            href={`https://t.me/${player.telegram_username}`}
            className="block rounded-xl bg-gradient-to-r from-violet-600 to-purple-500 py-4 text-center font-bold"
          >
            Написать в Telegram
          </a>
        )}
      </div>
    </Shell>
  );
}
function MatchScreen({
  first,
  second,
  close,
}: {
  first: Profile;
  second: PlayerCardData;
  close: () => void;
}) {
  return (
    <Shell>
      <div className="flex flex-1 flex-col items-center justify-center bg-[radial-gradient(circle,#29165a_0,transparent_45%)] px-6 text-center">
        <div className="text-6xl">🎉</div>
        <h1 className="mt-5 text-3xl font-bold">У вас мэтч!</h1>
        <p className="mt-3 text-slate-400">Вы понравились друг другу</p>
        <div className="my-12 flex items-center">
          <Avatar src={first.avatar_url} name={first.faceit_nickname} huge />
          <span className="-mx-1 text-6xl text-fuchsia-400">♡</span>
          <Avatar src={second.avatar_url} name={second.faceit_nickname} huge />
        </div>
        {second.telegram_username && (
          <a
            href={`https://t.me/${second.telegram_username}`}
            className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-purple-500 py-4 font-bold"
          >
            Написать в Telegram
          </a>
        )}
        <button onClick={close} className="mt-7 text-slate-400">
          Продолжить поиск
        </button>
      </div>
    </Shell>
  );
}
function ProfileForm({
  initial,
  onSaved,
  setError,
}: {
  initial?: Profile;
  onSaved: (p: Profile) => void;
  setError: (s: string) => void;
}) {
  const [role, setRole] = useState<(typeof roles)[number]>(
    (initial?.role as (typeof roles)[number]) ?? "Rifler",
  );
  const [bio, setBio] = useState(initial?.bio ?? "");
  const [saving, setSaving] = useState(false);
  const faceit = useFaceitConnect(setError);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const r = await api.patch<Profile>("/profile/me", {
        role,
        bio,
        is_searching: true,
      });
      onSaved(r.data);
    } catch (x) {
      setError(messageOf(x));
    } finally {
      setSaving(false);
    }
  }
  if (!initial)
    return (
      <div className="grid flex-1 place-items-center overflow-y-auto p-5">
        <section className="w-full max-w-xl rounded-3xl border border-white/10 bg-[#0d1724] p-6 text-center shadow-2xl">
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-2xl bg-[#ff5500] text-4xl font-black">
            F
          </div>
          <h1 className="mt-6 text-2xl font-bold">Подключите FACEIT</h1>
          <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
            Войдите через официальный сайт FACEIT. Никнейм, аватар, ELO и
            статистика загрузятся автоматически.
          </p>
          <button
            disabled={!faceit.ready}
            onClick={faceit.open}
            className="mt-8 w-full rounded-xl bg-gradient-to-r from-[#ff5500] to-orange-400 py-4 font-bold disabled:opacity-50"
          >
            {faceit.ready ? "Войти через FACEIT" : "Подготавливаем FACEIT…"}
          </button>
          <p className="mt-4 text-[11px] text-slate-600">
            Пароль вводится только на accounts.faceit.com
          </p>
        </section>
      </div>
    );
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <h1 className="mb-5 text-center text-xl font-bold">
        Редактировать профиль
      </h1>
      <form
        onSubmit={submit}
        className="mx-auto max-w-2xl space-y-4 rounded-2xl border border-white/10 bg-[#0d1724] p-4"
      >
        <div className="rounded-xl border border-white/10 bg-[#09131f] p-3">
          <p className="text-xs text-slate-500">FACEIT аккаунт</p>
          <p className="mt-1 font-bold">
            {initial.faceit_nickname}　
            <span className="text-green-400">Подключён</span>
          </p>
        </div>
        <Field label="О себе">
          <textarea
            value={bio}
            maxLength={500}
            onChange={(e) => setBio(e.target.value)}
            className="input min-h-28 resize-none"
          />
        </Field>
        <Field label="Роль">
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as typeof role)}
            className="input"
          >
            {roles.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </Field>
        <button
          disabled={saving}
          className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-purple-500 py-4 font-bold disabled:opacity-50"
        >
          {saving ? "Сохраняем…" : "Сохранить"}
        </button>
      </form>
    </div>
  );
}
function Stats({ elo, kd, level }: { elo: number; kd: number; level: number }) {
  return (
    <div className="mt-4 grid grid-cols-3 divide-x divide-white/10 rounded-xl border border-white/10 bg-[#09131f] py-4 text-center">
      <Stat label="ELO" value={`${elo}`} c="text-yellow-400" />
      <Stat label="K/D" value={kd.toFixed(2)} c="text-indigo-400" />
      <Stat label="LEVEL" value={`${level}`} c="text-green-400" />
    </div>
  );
}
function Stat({
  label,
  value,
  c,
}: {
  label: string;
  value: string;
  c: string;
}) {
  return (
    <div>
      <p className="text-[9px] text-slate-500">{label}</p>
      <p className={`text-xl font-bold ${c}`}>{value}</p>
    </div>
  );
}
function Small({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-2">
      <p className="text-[10px] text-slate-500">{label}</p>
      <p className="mt-1 text-sm">{value}</p>
    </div>
  );
}
function Avatar({
  src,
  name,
  big,
  huge,
}: {
  src: string | null;
  name: string;
  big?: boolean;
  huge?: boolean;
}) {
  const s = huge ? "h-28 w-28" : big ? "h-20 w-20" : "h-14 w-14";
  return src ? (
    <img
      src={src}
      className={`${s} shrink-0 rounded-full border-2 border-white object-cover`}
    />
  ) : (
    <div
      className={`${s} grid shrink-0 place-items-center rounded-full bg-violet-900 text-2xl font-bold`}
    >
      {name[0]}
    </div>
  );
}
function Panel({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#0d1724] p-3">
      {children}
    </div>
  );
}
function Row({ a, b, purple }: { a: string; b: string; purple?: boolean }) {
  return (
    <div className="flex justify-between border-b border-white/5 py-3 last:border-0">
      <span className="text-sm">{a}</span>
      <span className={purple ? "text-violet-400" : "text-xs text-slate-400"}>
        {b}
      </span>
    </div>
  );
}
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-2 text-sm font-semibold">
      <span>{label}</span>
      {children}
    </label>
  );
}
function Center({ text }: { text: string }) {
  return (
    <div className="grid min-h-72 place-items-center text-center text-slate-500">
      {text}
    </div>
  );
}
function Toast({ text, close }: { text: string; close: () => void }) {
  return (
    <button
      onClick={close}
      className="mx-4 mb-3 rounded-xl border border-rose-500/50 bg-rose-950/50 p-3 text-left text-sm text-rose-200"
    >
      {text}
    </button>
  );
}
function messageOf(e: unknown) {
  if (axios.isAxiosError(e)) {
    const d = e.response?.data?.detail;
    return typeof d === "string"
      ? d
      : `Ошибка сервера (${e.response?.status ?? "нет связи"})`;
  }
  return "Неизвестная ошибка";
}

function useFaceitConnect(onError?: (message: string) => void) {
  const [launchUrl, setLaunchUrl] = useState("");
  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    async function prepare(attempt = 0) {
      try {
        const response = await api.post<{ launch_url: string }>(
          "/faceit/oauth/start",
        );
        if (active) setLaunchUrl(response.data.launch_url);
      } catch (error) {
        if (!active) return;
        if (attempt < 5) timer = window.setTimeout(() => void prepare(attempt + 1), 1500);
        else (onError ?? window.alert)(messageOf(error));
      }
    }
    void prepare();
    return () => {
      active = false;
      if (timer) window.clearTimeout(timer);
    };
  }, []);

  function open() {
    if (launchUrl) openLink(launchUrl);
  }
  return { ready: Boolean(launchUrl), open };
}
