import { UsersRound } from "lucide-react";
export function EmptyState({title,text,action,label="CREATE PARTY"}:{title:string;text:string;action?:()=>void;label?:string}){return <div className="empty-state"><UsersRound/><b>{title}</b><p>{text}</p>{action&&<button className="secondary-action" onClick={action}>{label}</button>}</div>}
