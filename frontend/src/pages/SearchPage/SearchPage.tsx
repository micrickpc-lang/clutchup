import { SlidersHorizontal } from "lucide-react";
import type { PlayerDetails } from "../../types/api";
import { PageHeader } from "../../components/layout/AppLayout";
import { SwipeCard } from "../../components/player/SwipeCard";
import { EmptyState, ErrorState, Skeleton } from "../../components/ui/States";
import { GameSwitcher } from "../../components/game/GameSwitcher";
import { IntentPanel } from "../../components/party/IntentPanel";

export function SearchPage({ player, loading, busy, error, retry, swipe, details, filters }: { player: PlayerDetails | null; loading: boolean; busy: boolean; error: string; retry: () => void; swipe: (d: "like" | "dislike") => void; details: () => void; filters: () => void }) {
  return <><PageHeader title="CLUTCHUP" subtitle="PARTY SIGNAL / ONLINE" action={<button className="icon-button" onClick={filters} aria-label="Open filters"><SlidersHorizontal /></button>} /><section className="page-body search-body"><GameSwitcher/><IntentPanel openFilters={filters}/><div className="results-label"><span>03</span><strong>PLAYERS ON YOUR SIGNAL</strong></div>{loading ? <Skeleton tall /> : error ? <ErrorState message={error} retry={retry} /> : player ? <SwipeCard player={player} busy={busy} onSwipe={swipe} onDetails={details} /> : <EmptyState title="SIGNAL QUIET" text="Adjust your filters or check back soon." />}</section></>;
}
