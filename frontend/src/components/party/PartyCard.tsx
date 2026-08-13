import { Mic,Plus } from "lucide-react";
import { motion,useMotionValue,useReducedMotion,useSpring,useTransform } from "motion/react";
import type { PointerEvent } from "react";
import { cardVariants } from "../../motion/variants";
import type { Party } from "../../types/api";
import styles from "./PartyCard.module.css";

export function PartyCard({party,index=0,onJoin,onOpen}:{party:Party;index?:number;onJoin:(id:number)=>Promise<void>;onOpen:(party:Party)=>void}){
 const reduced=useReducedMotion(),x=useMotionValue(0),y=useMotionValue(0),rotateY=useSpring(useTransform(x,[-.5,.5],[-4,4])),rotateX=useSpring(useTransform(y,[-.5,.5],[3,-3]));
 const move=(event:PointerEvent<HTMLElement>)=>{if(reduced)return;const r=event.currentTarget.getBoundingClientRect();x.set((event.clientX-r.left)/r.width-.5);y.set((event.clientY-r.top)/r.height-.5)};
 const reset=()=>{x.set(0);y.set(0)};const requested=party.request_status==="PENDING";
 return <motion.article className={styles.card} custom={index} variants={cardVariants} initial="initial" animate="enter" exit="exit" onPointerMove={move} onPointerLeave={reset} style={reduced?undefined:{rotateX,rotateY,transformPerspective:900}}>
  <button className={styles.main} onClick={()=>onOpen(party)} aria-label={`Open ${party.title}`}>
   <div className={styles.top}><span>{party.mode}</span><time>{relativeTime(party.created_at)}</time></div>
   <div className={styles.need}><small>NEED</small><strong>+{party.free_slots}</strong></div>
   <h3>{party.title}</h3>
   <PartySlots party={party}/>
   <div className={styles.meta}>{party.mic_required&&<span><Mic/>MIC</span>}{party.language&&<span>{party.language.toUpperCase()}</span>}<span>{vibe(party.vibe)}</span>{party.rank_min!=null&&<span>RANK {party.rank_min}{party.rank_max!=null?`–${party.rank_max}`:"+"}</span>}</div>
  </button><motion.button whileTap={{scale:.97,y:1}} className={styles.action} disabled={requested||party.free_slots===0} onClick={()=>void onJoin(party.id)}>{requested?"REQUESTED":party.free_slots===0?"FULL":"+ PARTY"}</motion.button>
 </motion.article>
}
function PartySlots({party}:{party:Party}){return <div className={styles.slots}><div>{party.members.map(m=><span key={m.user_id}>{m.avatar_url?<img src={m.avatar_url} alt={m.display_name}/>:<b>{m.display_name.slice(0,1)}</b>}</span>)}{Array.from({length:party.free_slots},(_,i)=><i key={i}><Plus/></i>)}</div><strong>{party.current_members} / {party.capacity}</strong></div>}
function vibe(value:number){return value<40?"CHILL":value>70?"TRYHARD":"BALANCED"}
function relativeTime(value:string){const minutes=Math.max(0,Math.floor((Date.now()-new Date(value).getTime())/60000));return minutes<1?"NOW":minutes<60?`${minutes} MIN`:`${Math.floor(minutes/60)} HR`}
