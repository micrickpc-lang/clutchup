import { Plus } from "lucide-react";
import { useMemo } from "react";
import { useApp } from "../app/AppProvider";
import { useLocale } from "../i18n/LocaleProvider";
import type { Party } from "../types/api";
import { PartyFilters } from "../components/party/PartyFilters";
import { PartyFeed } from "../components/party/PartyFeed";
import { PartySearching } from "../components/party/PartySearching";
import { EmptyState } from "../components/ui/EmptyState";
export function FindPage({create,open}:{create:()=>void;open:(party:Party)=>void}){const app=useApp(),{t}=useLocale();const parties=useMemo(()=>app.parties.filter(p=>Math.abs(p.vibe-app.filters.vibe)<=35),[app.parties,app.filters.vibe]);return <section className="page"><h1 className="page-title">{t("findTitle").split("\n").map((line,index)=><span key={line}>{index>0&&<br/>}{line}</span>)}</h1><p className="page-copy">{t("findCopy",{name:app.gameProfile?.nickname||"your selected game"})}</p><PartyFilters game={app.game} value={app.filters} onChange={app.setFilters}/><div className="section-head"><h2>{t("openParties")}</h2><button className="text-action" onClick={create}><Plus/>{t("createParty")}</button></div>{app.loading?<PartySearching/>:parties.length?<PartyFeed items={parties} join={app.join} open={open}/>:<EmptyState title={t("noParties")} text={t("noPartiesText")} action={create} label={t("createParty")}/>}</section>}
