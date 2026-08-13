import { useCallback, useEffect, useState } from "react";
import { endpoints, errorMessage } from "./api/client";
import { TacticalApp } from "./components/TacticalApp";
import { ConnectFaceit } from "./features/faceit/ConnectFaceit";
import { usePresence } from "./features/presence/usePresence";
import { initializeTelegram } from "./lib/telegram";
import { MatchPage } from "./pages/MatchPage/MatchPage";
import { PlayerDetailsPage } from "./pages/PlayerDetailsPage/PlayerDetailsPage";
import { ProfileEditor } from "./pages/ProfilePage/ProfilePage";
import type { MatchItem, PlayerDetails, Profile, ProfileUpdate, SearchPreferences, Statistics, Tab } from "./types/api";

export default function App(){
 const [tab,setTab]=useState<Tab>("search"),[profile,setProfile]=useState<Profile|null>(),[card,setCard]=useState<PlayerDetails|null>(null),[matches,setMatches]=useState<MatchItem[]>([]),[preferences,setPreferences]=useState<SearchPreferences|null>(null),[statistics,setStatistics]=useState<Statistics|null>(null),[selected,setSelected]=useState<PlayerDetails|null>(null),[newMatch,setNewMatch]=useState<PlayerDetails|null>(null),[editing,setEditing]=useState(false),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState("");
 usePresence(Boolean(profile));
 const loadProfile=useCallback(async()=>{try{const p=await endpoints.profile();setProfile(p);return p}catch(e){setError(errorMessage(e));setProfile(null);return null}},[]);
 const loadCard=useCallback(async()=>{setLoading(true);try{setCard(await endpoints.nextCard())}catch(e){setError(errorMessage(e))}finally{setLoading(false)}},[]);
 const loadMatches=useCallback(async()=>{try{setMatches((await endpoints.matches()).items)}catch(e){setError(errorMessage(e))}},[]);
 useEffect(()=>{initializeTelegram();void loadProfile().then(p=>p?loadCard():setLoading(false))},[loadProfile,loadCard]);
 const openPlayer=async(id:number)=>{try{setSelected(await endpoints.player(id))}catch(e){setError(errorMessage(e))}};
 const swipe=async(direction:"like"|"dislike")=>{if(!card||busy)return;setBusy(true);try{const r=await endpoints.swipe(card.user_id,direction);if(r.new_match&&r.match)setNewMatch(r.match);await loadCard();if(r.matched)void loadMatches()}catch(e){setError(errorMessage(e))}finally{setBusy(false)}};
 if(profile===undefined)return <div className="cu-boot">CLUTCHUP<span>ACQUIRING SIGNAL</span></div>;
 if(!profile)return <div className="cu-auth"><ConnectFaceit onConnected={p=>{setProfile(p);void loadCard()}} error={setError}/>{error&&<p>{error}</p>}</div>;
 if(newMatch)return <MatchPage me={profile} other={newMatch} close={()=>setNewMatch(null)}/>;
 if(selected)return <PlayerDetailsPage player={selected} close={()=>setSelected(null)}/>;
 if(editing)return <ProfileEditor profile={profile} busy={busy} close={()=>setEditing(false)} save={async(data:ProfileUpdate)=>{setBusy(true);try{setProfile(await endpoints.updateProfile(data));setEditing(false)}finally{setBusy(false)}}}/>;
 return <TacticalApp profile={profile} player={card} matches={matches} preferences={preferences} statistics={statistics} loading={loading} busy={busy} tab={tab} onTab={async next=>{setTab(next);if(next==="statistics"&&!preferences){try{const [p,s]=await Promise.all([endpoints.preferences(),endpoints.statistics()]);setPreferences(p);setStatistics(s)}catch(e){setError(errorMessage(e))}}}} onSwipe={swipe} onLoadMatches={loadMatches} onSaveFilters={async p=>{setPreferences(await endpoints.updatePreferences(p));await loadCard()}} onEdit={()=>setEditing(true)} onSettings={()=>setEditing(true)} onOpenPlayer={openPlayer}/>;
}
