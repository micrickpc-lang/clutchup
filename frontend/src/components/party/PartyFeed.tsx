import { AnimatePresence } from "motion/react";
import type { Party } from "../../types/api";
import { PartyCard } from "./PartyCard";
import styles from "./PartyFeed.module.css";
export function PartyFeed({items,join,open}:{items:Party[];join:(id:number)=>Promise<void>;open:(party:Party)=>void}){return <div className={styles.feed}><AnimatePresence mode="popLayout">{items.map((party,index)=><PartyCard key={party.id} party={party} index={index} onJoin={join} onOpen={open}/>)}</AnimatePresence></div>}
