import { Inbox,Search,UserRound,UsersRound } from "lucide-react";
import { motion } from "motion/react";
import type { AppTab } from "../../types/api";
import styles from "./BottomNav.module.css";
const items:[AppTab,string,typeof Search][]=[["find","FIND",Search],["parties","PARTIES",UsersRound],["inbox","INBOX",Inbox],["profile","PROFILE",UserRound]];
export function BottomNav({value,onChange}:{value:AppTab;onChange:(tab:AppTab)=>void}){return <nav className={styles.nav}>{items.map(([id,label,Icon])=><button key={id} className={value===id?styles.active:""} onClick={()=>onChange(id)} aria-current={value===id?"page":undefined}>{value===id&&<motion.i layoutId="nav-marker" transition={{type:"spring",stiffness:380,damping:34}}/>}<Icon/><span>{label}</span></button>)}</nav>}
