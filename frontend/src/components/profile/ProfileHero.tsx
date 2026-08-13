import { Mic } from "lucide-react";
import { countryFlag } from "../../i18n/country";
import { useLocale } from "../../i18n/LocaleProvider";
import type { UserProfile } from "../../types/api";
import styles from "./Profile.module.css";
export function ProfileHero({user}:{user:UserProfile}){const {t}=useLocale();return <section className={styles.hero}><div className={styles.portrait}>{user.avatar_url?<img src={user.avatar_url} alt={user.display_name}/>:<span>{user.display_name.slice(0,1)}</span>}<i/></div><div><small>CLUTCHUP PROFILE</small><h1>{countryFlag(user.country_code)} {user.display_name}</h1><p>{user.country_code||t("regionMissing")} · {user.languages.join(" / ")||t("languageMissing")}</p>{user.microphone&&<b><Mic/>{t("micReady")}</b>}</div></section>}
