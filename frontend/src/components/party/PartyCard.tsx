import { Mic,Plus,UsersRound } from "lucide-react";
import type { Party } from "../../types/api";

export function PartyCard({party,onJoin,onOpen}:{party:Party;onJoin:(id:number)=>Promise<void>;onOpen:(party:Party)=>void}){
 const requested=party.request_status==="PENDING";
 return <article className="party-card">
  <button className="party-card-main" onClick={()=>onOpen(party)} aria-label={`Open ${party.title}`}>
   <div className="party-card-top"><span>{party.mode}</span><strong>NEED +{party.free_slots}</strong></div>
   <h3>{party.title}</h3>
   <div className="party-slots" aria-label={`${party.current_members} of ${party.capacity} players`}>
    {party.members.map(member=><img key={member.user_id} src={member.avatar_url||"/assets/tactical-operator.png"} alt={member.display_name}/>)}
    {Array.from({length:party.free_slots},(_,i)=><i key={i}><Plus/></i>)}
    <b><UsersRound/>{party.current_members} / {party.capacity}</b>
   </div>
   <div className="party-meta">{party.mic_required&&<span><Mic/> MIC</span>}{party.language&&<span>{party.language.toUpperCase()}</span>}<span>{party.vibe<40?"CHILL":party.vibe>70?"TRYHARD":"BALANCED"}</span>{party.rank_min!=null&&<span>RANK {party.rank_min}{party.rank_max!=null?`–${party.rank_max}`:"+"}</span>}</div>
  </button>
  <button className={`party-request ${requested?"requested":""}`} disabled={requested||party.free_slots===0} onClick={()=>void onJoin(party.id)}>{requested?"REQUESTED":party.free_slots===0?"FULL":"+ PARTY"}</button>
 </article>
}
