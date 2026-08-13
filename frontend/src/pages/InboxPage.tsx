import { useApp } from "../app/AppProvider";
import { InboxItem } from "../components/inbox/InboxItem";
import { EmptyState } from "../components/ui/EmptyState";
export function InboxPage(){const app=useApp();return <section className="page"><h1 className="page-title">INBOX</h1><p className="page-copy">Join requests and party activity.</p><div className="section-head"><h2>ACTIVITY</h2></div>{app.requests.length?<div style={{display:"grid",gap:10}}>{app.requests.map(r=><InboxItem key={r.id} request={r} own={r.requester_user_id===app.user?.user_id} decide={app.decide}/>)}</div>:<EmptyState title="INBOX IS CLEAR" text="New join requests and updates will appear here."/>}</section>}
