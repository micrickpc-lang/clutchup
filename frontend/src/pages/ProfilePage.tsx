import { useApp } from "../app/AppProvider";
import { GAME_IDS } from "../config/games";
import { useLocale } from "../i18n/LocaleProvider";
import { FaceitCard } from "../components/profile/FaceitCard";
import { GameProfileCard } from "../components/profile/GameProfileCard";
import { LanguageSettings } from "../components/profile/LanguageSettings";
import { ProfileHero } from "../components/profile/ProfileHero";
export function ProfilePage(){const app=useApp(),{t}=useLocale();if(!app.user)return <section className="page"><div className="skeleton"/></section>;const cs2=app.gameProfiles.find(profile=>profile.game==="cs2")||null;return <section className="page"><ProfileHero user={app.user}/><h2 style={{font:"700 12px var(--font-tech)",letterSpacing:".1em",marginBottom:14}}>{t("gameProfiles")}</h2><div style={{display:"grid",gap:9}}>{GAME_IDS.map(game=><GameProfileCard key={game} game={game} countryCode={app.user?.country_code} profile={app.gameProfiles.find(profile=>profile.game===game)||null}/>)}</div><FaceitCard connected={app.user.faceit_connected} profile={cs2}/><div className="section-head"><h2>{t("settings")}</h2></div><LanguageSettings/></section>}
