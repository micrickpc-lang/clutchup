import { ChevronDown } from "lucide-react";
import { GAME_CONFIG } from "../../config/games";
import type { GameId } from "../../types/api";
import styles from "./AppHeader.module.css";
export function AppHeader({game,onGame}:{game:GameId;onGame:()=>void}){return <header className={styles.header}><div className={styles.brand}><i/>CLUTCH<span>UP</span><small>FIND. JOIN. PLAY.</small></div><button onClick={onGame} aria-label="Change game">{GAME_CONFIG[game].shortName}<ChevronDown/></button></header>}
