import { MessageSquare, Search, UsersRound, UserRound } from "lucide-react";
import type { ReactNode } from "react";
import type { Tab } from "../../types/api";

const items = [
  { id: "search", label: "FIND", Icon: Search },
  { id: "matches", label: "PARTIES", Icon: UsersRound },
  { id: "statistics", label: "INBOX", Icon: MessageSquare },
  { id: "profile", label: "PROFILE", Icon: UserRound },
] as const;

export function AppLayout({ children, tab, onTab }: { children: ReactNode; tab?: Tab; onTab?: (tab: Tab) => void }) {
  return <main className="app-shell"><div className="ambient-grid" aria-hidden /><div className="app-content">{children}</div>{tab && onTab && <nav className="bottom-nav" aria-label="Main navigation">{items.map(({ id, label, Icon }) => <button key={id} className={tab === id ? "active" : ""} onClick={() => onTab(id)} aria-current={tab === id ? "page" : undefined}><Icon size={20} aria-hidden /><span>{label}</span></button>)}</nav>}</main>;
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) { return <header className="page-header"><div className="brand-mark" aria-hidden><i />C</div><div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div><div className="header-action">{action}</div></header>; }
