import { GAME_CONFIG } from "../../config/games";
import { countryFlag } from "../../i18n/country";
import { useLocale } from "../../i18n/LocaleProvider";
import type { GameId,GameProfile } from "../../types/api";
import styles from "./Profile.module.css";
export function GameProfileCard({game,profile,countryCode}:{game:GameId;profile:GameProfile|null;countryCode?:string|null}){const cfg=GAME_CONFIG[game],{t}=useLocale();return <article className={styles.gameCard+" "+styles[game]}><i/><small>{cfg.displayName}</small><strong>{profile?countryFlag(countryCode)+" "+profile.nickname:t("notConfigured")}</strong><span>{profile?.primary_role||cfg.modes[0]}</span></article>}
