import { useState } from "react";
import type { CSSProperties } from "react";

const games = [
  { id: "CS2", tone: "amber", mark: "CS", sub: "COUNTER-STRIKE 2" },
  { id: "VALORANT", tone: "red", mark: "V", sub: "TACTICAL 5V5" },
  { id: "STANDOFF 2", tone: "orange", mark: "S2", sub: "MOBILE FPS" },
] as const;

export function GameSwitcher() {
  const [active, setActive] = useState(0);
  return <section className="game-section"><div className="section-kicker"><span>01</span><div><strong>CHOOSE YOUR GAME</strong><small>SELECT YOUR SIGNAL</small></div></div><div className="game-deck">{games.map((game, index) => { const delta = index - active; return <button key={game.id} className={`game-card ${game.tone} ${delta === 0 ? "selected" : ""}`} style={{ "--offset": delta } as CSSProperties} onClick={() => setActive(index)} aria-pressed={delta === 0}><span className="game-no">0{index + 1}</span><b>{game.mark}</b><strong>{game.id}</strong><small>{game.sub}</small></button>; })}</div><div className="deck-dots">{games.map((g,i)=><button key={g.id} onClick={()=>setActive(i)} className={i===active?"active":""} aria-label={`Choose ${g.id}`} />)}</div></section>;
}
