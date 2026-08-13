import { AnimatePresence,motion } from "motion/react";
import { useState } from "react";
import { useApp } from "../../app/AppProvider";
import { useLocale } from "../../i18n/LocaleProvider";
import { pageVariants } from "../../motion/variants";
import type { Party } from "../../types/api";
import { FindPage } from "../../pages/FindPage";
import { InboxPage } from "../../pages/InboxPage";
import { PartiesPage } from "../../pages/PartiesPage";
import { ProfilePage } from "../../pages/ProfilePage";
import { GameSwitcher } from "../game/GameSwitcher";
import { CreatePartySheet } from "../party/CreatePartySheet";
import { PartyDetailSheet } from "../party/PartyDetailSheet";
import { PartyFoundScene } from "../party/PartyFoundScene";
import { Sheet } from "../ui/Sheet";
import { AppHeader } from "./AppHeader";
import { BottomNav } from "./BottomNav";
export function ProductShell(){const app=useApp(),{t}=useLocale();const [gameOpen,setGameOpen]=useState(false),[createOpen,setCreateOpen]=useState(false),[selected,setSelected]=useState<Party|null>(null);const page=app.tab==="find"?<FindPage create={()=>setCreateOpen(true)} open={setSelected}/>:app.tab==="parties"?<PartiesPage create={()=>setCreateOpen(true)} open={setSelected}/>:app.tab==="inbox"?<InboxPage/>:<ProfilePage/>;return <main className="product-shell"><AppHeader game={app.game} onGame={()=>setGameOpen(true)}/><div className="product-scroll" aria-live="polite">{app.error&&<div className="api-error">COULDN'T LOAD PARTIES<button onClick={()=>void app.reload()}>RETRY</button></div>}<AnimatePresence mode="wait"><motion.div key={app.tab+"-"+app.game} variants={pageVariants} initial="initial" animate="enter" exit="exit">{page}</motion.div></AnimatePresence></div><BottomNav value={app.tab} onChange={app.setTab}/><AnimatePresence>{gameOpen&&<Sheet title={t("chooseGame")} close={()=>setGameOpen(false)}><GameSwitcher value={app.game} onChange={app.setGame} onResolved={()=>setGameOpen(false)}/></Sheet>}{createOpen&&<CreatePartySheet close={()=>setCreateOpen(false)}/>} {selected&&<PartyDetailSheet party={selected} close={()=>setSelected(null)} join={app.join}/>} {app.partyFound&&<PartyFoundScene party={app.partyFound} close={app.clearPartyFound} open={()=>{setSelected(app.partyFound);app.clearPartyFound()}}/>}</AnimatePresence></main>}
