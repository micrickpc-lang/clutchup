import { endpoints } from "../../api/client";
import type { GameProfile } from "../../types/api";
import styles from "./Profile.module.css";
export function FaceitCard({connected,profile}:{connected:boolean;profile:GameProfile|null}){const connect=async()=>{if(connected)return;const {authorization_url}=await endpoints.oauthStart();location.assign(authorization_url)};return <article className={styles.faceit}><small>FACEIT · OPTIONAL CS2 INTEGRATION</small><strong>{connected?"CONNECTED":"CONNECT FACEIT"}</strong>{connected&&profile?.rank_value!=null&&<span>{profile.rank_value} ELO · {profile.rank_label}</span>}<button disabled={connected} onClick={()=>void connect()}>{connected?"CONNECTED":"CONNECT"}</button></article>}
