import { Heart, MessageCircle } from "lucide-react";
import { Avatar } from "../../components/ui/Avatar";
import { telegramChat } from "../../lib/telegram";
import type { PlayerDetails, Profile } from "../../types/api";

export function MatchPage({ me, other, close }: { me: Profile; other: PlayerDetails; close: () => void }) {
  const metrics: [string, string, string][] = [["ELO", `${me.statistics.elo}`, `${other.statistics.elo}`], ["K/D", value(me.statistics.kd_ratio, 2), value(other.statistics.kd_ratio, 2)], ["ADR", value(me.statistics.adr, 1), value(other.statistics.adr, 1)], ["Победы", value(me.statistics.win_rate, 0, "%"), value(other.statistics.win_rate, 0, "%")]];
  return <section className="match-page"><div className="confetti" aria-hidden /><h1>У вас мэтч!</h1><p>Вы понравились друг другу</p><div className="match-avatars"><div><Avatar src={me.avatar_url} name={me.faceit_nickname} size="xl" /><strong>{me.faceit_nickname}</strong></div><span><Heart fill="currentColor" /></span><div><Avatar src={other.avatar_url} name={other.faceit_nickname} size="xl" /><strong>{other.faceit_nickname}</strong></div></div><div className="comparison">{metrics.map(([label, a, b]) => <div key={label}><strong>{a}</strong><span>{label}</span><strong>{b}</strong></div>)}</div>{other.telegram_username && <button className="button primary" onClick={() => telegramChat(other.telegram_username!)}><MessageCircle />Открыть чат в Telegram</button>}<button className="button ghost" onClick={close}>Продолжить поиск</button></section>;
}
function value(input: number | null, digits: number, suffix = "") { return input == null ? "—" : `${input.toFixed(digits)}${suffix}`; }
