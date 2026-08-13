import { useApp } from "../app/AppProvider";
import { GAME_IDS } from "../config/games";
import { FaceitCard } from "../components/profile/FaceitCard";
import { GameProfileCard } from "../components/profile/GameProfileCard";
import { ProfileHero } from "../components/profile/ProfileHero";
export function ProfilePage(){const app=useApp();if(!app.user)return <section className="page"><div className="skeleton"/></section>;return <section className="page"><ProfileHero user={app.user}/><h2 style={{font:"700 12px var(--font-tech)",letterSpacing:".1em",marginBottom:14}}>GAME PROFILES</h2><div style={{display:"grid",gap:9}}>{GAME_IDS.map(game=><GameProfileCard key={game} game={game} profile={game===app.game?app.gameProfile:null}/>)}</div><FaceitCard connected={app.user.faceit_connected} profile={app.gameProfile?.game==="cs2"?app.gameProfile:null}/></section>}
