import { Inbox,Search,UserRound,UsersRound } from "lucide-react";
import { motion } from "motion/react";
import { useLocale } from "../../i18n/LocaleProvider";
import type { AppTab } from "../../types/api";
import styles from "./BottomNav.module.css";
const items=[["find","find",Search],["parties","parties",UsersRound],["inbox","inbox",Inbox],["profile","profile",UserRound]] as const;
export function BottomNav({value,onChange}:{value:AppTab;onChange:(tab:AppTab)=>void}){const {t}=useLocale();return <nav className={styles.nav}>{items.map(([id,label,Icon])=><button key={id} className={value===id?styles.active:""} onClick={()=>onChange(id)} aria-current={value===id?"page":undefined}>{value===id&&<motion.i layoutId="nav-marker" transition={{type:"spring",stiffness:380,damping:34}}/>}<Icon/><span>{t(label)}</span></button>)}</nav>}
