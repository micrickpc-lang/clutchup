import type { CSSProperties } from "react";
import { GAME_CONFIG,GAME_IDS } from "../../config/games";
import type { GameId } from "../../types/api";
export function ControlledGameSwitcher({value,onChange}:{value:GameId;onChange:(v:GameId)=>void}){const active=GAME_IDS.indexOf(value);return <div className="controlled-deck">{GAME_IDS.map((id,index)=>{const game=GAME_CONFIG[id];return <button key={id} className={`${game.tone} ${id===value?"active":""}`} style={{"--offset":index-active} as CSSProperties} onClick={()=>onChange(id)}><img src="/assets/tactical-operator.png" alt=""/><strong>{game.shortName}</strong><small>{game.displayName}</small></button>})}</div>}
