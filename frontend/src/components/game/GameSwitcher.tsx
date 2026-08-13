import { motion,useReducedMotion } from "motion/react";
import { GAME_CONFIG,GAME_IDS } from "../../config/games";
import { spring } from "../../motion/tokens";
import type { GameId } from "../../types/api";
import styles from "./GameSwitcher.module.css";

export function GameSwitcher({value="cs2",onChange=()=>undefined}:{value?:GameId;onChange?:(value:GameId)=>void}){
 const active=GAME_IDS.indexOf(value),reduced=useReducedMotion();
 return <div className={styles.deck}>{GAME_IDS.map((id,index)=>{const offset=index-active,cfg=GAME_CONFIG[id];return <motion.button key={id} className={`${styles.card} ${styles[id]} ${id===value?styles.active:""}`} animate={reduced?{opacity:id===value?1:.58}:{x:offset*112,scale:id===value?1:.87,rotateY:offset*-15,z:id===value?58:-35,opacity:id===value?1:.58}} transition={spring.panel} whileTap={{scale:.98}} onClick={()=>onChange(id)} aria-pressed={id===value}><div className={styles.backdrop}/><div className={styles.art}><i/><i/><i/></div><div className={styles.copy}><small>{cfg.displayName}</small><strong>{cfg.shortName}</strong><span>{cfg.modes.join(" · ")}</span></div>{id===value&&<motion.em layoutId="game-edge"/>}</motion.button>})}</div>
}
