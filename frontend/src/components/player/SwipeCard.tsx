import { ArrowUpRight, Mic, Radio, UserPlus, X } from "lucide-react";
import { useRef, useState } from "react";
import type { PointerEvent } from "react";
import type { PlayerDetails } from "../../types/api";

export function SwipeCard({ player, busy, onSwipe, onDetails }: { player: PlayerDetails; busy: boolean; onSwipe: (direction: "like" | "dislike") => void; onDetails: () => void }) {
  const start = useRef(0); const [offset, setOffset] = useState(0); const [leaving,setLeaving]=useState(false); const dragging = useRef(false);
  const down = (e: PointerEvent<HTMLElement>) => { if (busy) return; dragging.current = true; start.current = e.clientX; e.currentTarget.setPointerCapture(e.pointerId); };
  const move = (e: PointerEvent<HTMLElement>) => { if (dragging.current) setOffset(Math.max(-180, Math.min(180, e.clientX - start.current))); };
  const act=(direction:"like"|"dislike")=>{ if(direction==="like"){ onSwipe(direction); return; } setLeaving(true); window.setTimeout(()=>{onSwipe(direction);setLeaving(false)},260); };
  const up = () => { if (!dragging.current) return; dragging.current = false; if (Math.abs(offset) >= 85) act(offset > 0 ? "like" : "dislike"); setOffset(0); };
  const age = player.birth_year ? new Date().getFullYear()-player.birth_year : null;
  return <div className="card-stage"><div className="stack-card stack-two"/><div className="stack-card stack-one"/><article className={`swipe-card ${leaving?"signal-lost":""}`} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} style={{ transform: `translateX(${offset}px) rotate(${offset / 30}deg)` }}>
    <div className="player-hero">{player.avatar_url ? <img src={player.avatar_url} alt={player.faceit_nickname} draggable={false} /> : <div className="hero-fallback">{player.faceit_nickname.slice(0, 1).toUpperCase()}</div>}<div className="hero-shade" /><span className={`presence ${player.is_online ? "online" : ""}`}><Radio/> {player.is_online ? "ONLINE" : "OFFLINE"}</span><div className="hero-name"><div className="eyebrow">MATCH SIGNAL • ~12m</div><h2>{player.faceit_nickname} {age && <small>{age}</small>}</h2><p>{player.country_code || "EUROPE"} / {player.languages.join(" · ") || "EN"}</p></div></div>
    <div className="tactical-data"><div className="role-line"><span>{player.primary_role}</span>{player.secondary_role&&<span>{player.secondary_role}</span>}<b>LVL {player.statistics.skill_level}</b></div><div className="trust-line"><i/> FACEIT <strong>{player.statistics.elo} ELO</strong></div><p>{player.bio || "Ready to queue. Clear comms, team play, no noise."}</p><div className="signal-chips"><span>COMPETITIVE</span><span>{player.playstyle || "BALANCED"}</span>{player.microphone&&<span><Mic/> MIC</span>}</div></div>
    <div className="swipe-actions"><button disabled={busy} onClick={()=>act("dislike")} className="dislike" aria-label="Pass player"><X/><span>PASS</span></button><button onClick={onDetails} className="details"><ArrowUpRight/><span>PROFILE</span></button><button disabled={busy} onClick={()=>act("like")} className="like" aria-label="Add to party"><UserPlus/><span>+ PARTY</span></button></div>
  </article></div>;
}
