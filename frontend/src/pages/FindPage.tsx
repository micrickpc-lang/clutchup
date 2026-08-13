import { Plus } from "lucide-react";
import { useMemo } from "react";
import { useApp } from "../app/AppProvider";
import type { Party } from "../types/api";
import { PartyFeed } from "../components/party/PartyFeed";
import { PartySearching } from "../components/party/PartySearching";
import { PartyFilters } from "../components/party/PartyFilters";
import { EmptyState } from "../components/ui/EmptyState";
export function FindPage({create,open}:{create:()=>void;open:(party:Party)=>void}){const app=useApp();const parties=useMemo(()=>app.parties.filter(p=>Math.abs(p.vibe-app.filters.vibe)<=35),[app.parties,app.filters.vibe]);return <section className="page"><h1 className="page-title">FIND<br/>YOUR PARTY</h1><p className="page-copy">Open parties for {app.gameProfile?.nickname||"your selected game"}. Join in seconds.</p><PartyFilters game={app.game} value={app.filters} onChange={app.setFilters}/><div className="section-head"><h2>OPEN PARTIES</h2><button className="text-action" onClick={create}><Plus/>CREATE PARTY</button></div>{app.loading?<PartySearching/>:parties.length?<PartyFeed items={parties} join={app.join} open={open}/>:<EmptyState title="NO OPEN PARTIES" text="Try another mode or create your own party." action={create}/>}</section>}
