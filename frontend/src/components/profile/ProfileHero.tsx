import { Mic } from "lucide-react";
import type { UserProfile } from "../../types/api";
import styles from "./Profile.module.css";
export function ProfileHero({user}:{user:UserProfile}){return <section className={styles.hero}><div className={styles.portrait}>{user.avatar_url?<img src={user.avatar_url} alt={user.display_name}/>:<span>{user.display_name.slice(0,1)}</span>}<i/></div><div><small>CLUTCHUP PROFILE</small><h1>{user.display_name}</h1><p>{user.country_code||"REGION NOT SET"} · {user.languages.join(" / ")||"LANGUAGE NOT SET"}</p>{user.microphone&&<b><Mic/>MIC READY</b>}</div></section>}
