import { Plus } from "lucide-react";
import { useState } from "react";
import { useApp } from "../app/AppProvider";
import { useLocale } from "../i18n/LocaleProvider";
import type { Party } from "../types/api";
import { InboxItem } from "../components/inbox/InboxItem";
import { PartyFeed } from "../components/party/PartyFeed";
import { EmptyState } from "../components/ui/EmptyState";
import styles from "./PartiesPage.module.css";
type View="active"|"invites"|"history";
export function PartiesPage({create,open}:{create:()=>void;open:(party:Party)=>void}){const app=useApp(),{t}=useLocale(),[view,setView]=useState<View>("active");const pending=app.requests.filter(request=>request.status==="PENDING"),history=app.requests.filter(request=>request.status!=="PENDING"),shown=view==="invites"?pending:history;return <section className="page"><div className="section-head"><h1 className="page-title">{t("myParties")}</h1><button className="text-action" onClick={create}><Plus/>{t("create")}</button></div><div className={styles.tabs}>{(["active","invites","history"] as View[]).map(item=><button key={item} className={view===item?styles.active:""} onClick={()=>setView(item)}>{t(item)}</button>)}</div>{view==="active"?(app.mine.length?<PartyFeed items={app.mine} join={app.join} open={open}/>:<EmptyState title={t("noActive")} text={t("noActiveText")} action={create} label={t("createParty")}/>):<div style={{display:"grid",gap:10}}>{shown.map(request=><InboxItem key={request.id} request={request} own={request.requester_user_id===app.user?.user_id} decide={app.decide}/>)}{!shown.length&&<EmptyState title={view==="invites"?"NO INVITES":"NO HISTORY"} text={view==="invites"?"New party invitations will appear here.":"Completed requests will appear here."}/>}</div>}</section>}
