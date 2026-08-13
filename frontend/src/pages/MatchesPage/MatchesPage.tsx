import { MessageCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { PageHeader } from "../../components/layout/AppLayout";
import { Avatar } from "../../components/ui/Avatar";
import { EmptyState, ErrorState, Skeleton } from "../../components/ui/States";
import { telegramChat } from "../../lib/telegram";
import type { MatchItem } from "../../types/api";

type Filter = "all" | "new" | "online";
export function MatchesPage({ items, loading, error, retry, select }: { items: MatchItem[]; loading: boolean; error: string; retry: () => void; select: (id: number) => void }) {
  const [filter, setFilter] = useState<Filter>("all");
  const shown = useMemo(() => items.filter((item) => filter === "all" || (filter === "new" ? item.is_new_match : item.is_online)), [items, filter]);
  return <><PageHeader title="Матчи" /><section className="page-body"><div className="segmented" role="tablist">{([['all','Все'],['new','Новые'],['online','Онлайн']] as const).map(([id, label]) => <button role="tab" aria-selected={filter === id} className={filter === id ? "active" : ""} onClick={() => setFilter(id)} key={id}>{label}</button>)}</div>{loading ? <Skeleton tall /> : error ? <ErrorState message={error} retry={retry} /> : shown.length === 0 ? <EmptyState title="Матчей пока нет" text={filter === "all" ? "Взаимные лайки появятся здесь." : "В этой категории ничего нет."} /> : <div className="match-list">{shown.map((item) => <article className="match-item" key={item.user_id}><button className="match-main" onClick={() => select(item.user_id)}><Avatar src={item.avatar_url} name={item.faceit_nickname} /><span><strong>{item.faceit_nickname}{item.is_new_match && <i>Новый</i>}</strong><small className={item.is_online ? "online-text" : ""}>{item.is_online ? "Онлайн" : `ELO ${item.statistics.elo}`}</small></span></button>{item.telegram_username && <button className="chat-button" aria-label={`Написать ${item.faceit_nickname}`} onClick={() => telegramChat(item.telegram_username!)}><MessageCircle /></button>}</article>)}</div>}</section></>;
}
