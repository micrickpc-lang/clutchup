import { GAME_CONFIG } from "../../config/games";
import type { GameId,GameProfile } from "../../types/api";
import styles from "./Profile.module.css";
export function GameProfileCard({game,profile}:{game:GameId;profile:GameProfile|null}){const cfg=GAME_CONFIG[game];return <article className={`${styles.gameCard} ${styles[game]}`}><i/><small>{cfg.displayName}</small><strong>{profile?.nickname||"NOT CONFIGURED"}</strong><span>{profile?.primary_role||cfg.modes[0]}</span></article>}
