import { Plus } from "lucide-react";
import { useApp } from "../app/AppProvider";
import type { Party } from "../types/api";
import { PartyFeed } from "../components/party/PartyFeed";
import { EmptyState } from "../components/ui/EmptyState";
import styles from "./PartiesPage.module.css";
export function PartiesPage({create,open}:{create:()=>void;open:(party:Party)=>void}){const app=useApp();return <section className="page"><div className="section-head"><h1 className="page-title">MY PARTIES</h1><button className="text-action" onClick={create}><Plus/>CREATE</button></div><div className={styles.tabs}><button className={styles.active}>ACTIVE</button><button>INVITES</button><button>HISTORY</button></div>{app.mine.length?<PartyFeed items={app.mine} join={app.join} open={open}/>:<EmptyState title="NO ACTIVE PARTIES" text="Create a party or request to join one from Find." action={create}/>}</section>}
