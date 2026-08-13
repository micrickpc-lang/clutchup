import { useCallback, useEffect, useState } from "react";
import { endpoints, errorMessage } from "./api/client";
import { AppLayout } from "./components/layout/AppLayout";
import { Toast } from "./components/ui/States";
import { ConnectFaceit } from "./features/faceit/ConnectFaceit";
import { usePresence } from "./features/presence/usePresence";
import { initializeTelegram } from "./lib/telegram";
import { MatchPage } from "./pages/MatchPage/MatchPage";
import { MatchesPage } from "./pages/MatchesPage/MatchesPage";
import { PlayerDetailsPage } from "./pages/PlayerDetailsPage/PlayerDetailsPage";
import { ProfileEditor, ProfilePage } from "./pages/ProfilePage/ProfilePage";
import { SearchPage } from "./pages/SearchPage/SearchPage";
import { SettingsPage } from "./pages/SettingsPage/SettingsPage";
import { StatisticsPage } from "./pages/StatisticsPage/StatisticsPage";
import type { MatchItem, PlayerDetails, Profile, ProfileUpdate, SearchPreferences, Statistics, Tab } from "./types/api";

export default function App() {
  const [tab, setTab] = useState<Tab>("search"); const [profile, setProfile] = useState<Profile | null>(); const [card, setCard] = useState<PlayerDetails | null>(null); const [matches, setMatches] = useState<MatchItem[]>([]); const [preferences, setPreferences] = useState<SearchPreferences | null>(null); const [statistics, setStatistics] = useState<Statistics | null>(null); const [selected, setSelected] = useState<PlayerDetails | null>(null); const [newMatch, setNewMatch] = useState<PlayerDetails | null>(null); const [editing, setEditing] = useState(false); const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  usePresence(Boolean(profile));
  const loadProfile = useCallback(async () => { try { const value = await endpoints.profile(); setProfile(value); return value; } catch (e) { setError(errorMessage(e)); setProfile(null); return null; } }, []);
  const loadCard = useCallback(async () => { setLoading(true); try { setCard(await endpoints.nextCard()); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } }, []);
  const loadMatches = useCallback(async () => { setLoading(true); try { setMatches((await endpoints.matches()).items); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } }, []);
  const loadStatistics = useCallback(async () => { setLoading(true); try { const [p, s] = await Promise.all([endpoints.preferences(), endpoints.statistics()]); setPreferences(p); setStatistics(s); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } }, []);
  useEffect(() => { initializeTelegram(); void loadProfile().then((p) => { if (p) void loadCard(); else setLoading(false); }); }, [loadProfile, loadCard]);
  useEffect(() => { const refresh = () => { if (document.visibilityState === "visible") void loadProfile(); }; window.addEventListener("focus", refresh); document.addEventListener("visibilitychange", refresh); return () => { window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); }; }, [loadProfile]);
  const navigate = (next: Tab) => { setTab(next); setError(""); if (next === "matches") void loadMatches(); if (next === "statistics") void loadStatistics(); };
  const swipe = async (direction: "like" | "dislike") => { if (!card || busy) return; setBusy(true); const old = card; try { const result = await endpoints.swipe(card.user_id, direction); if (result.new_match && result.match) setNewMatch(result.match); setCard(null); await loadCard(); if (result.matched) void loadMatches(); } catch (e) { setCard(old); setError(errorMessage(e)); } finally { setBusy(false); } };
  const openPlayer = async (id: number) => { try { setSelected(await endpoints.player(id)); } catch (e) { setError(errorMessage(e)); } };
  if (profile === undefined) return <AppLayout><div className="launch-skeleton" /></AppLayout>;
  if (!profile) return <AppLayout><ConnectFaceit onConnected={(connected) => { setProfile(connected); void loadCard(); }} error={setError} />{error && <Toast message={error} close={() => setError("")} />}</AppLayout>;
  if (newMatch) return <AppLayout><MatchPage me={profile} other={newMatch} close={() => setNewMatch(null)} /></AppLayout>;
  if (selected) return <AppLayout><PlayerDetailsPage player={selected} close={() => setSelected(null)} /></AppLayout>;
  if (editing) return <AppLayout><ProfileEditor profile={profile} busy={busy} close={() => setEditing(false)} save={async (data: ProfileUpdate) => { setBusy(true); try { setProfile(await endpoints.updateProfile(data)); setEditing(false); } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); } }} />{error && <Toast message={error} close={() => setError("")} />}</AppLayout>;
  return <AppLayout tab={tab} onTab={navigate}>{error && <Toast message={error} close={() => setError("")} />}{tab === "search" && <SearchPage player={card} loading={loading} busy={busy} error="" retry={loadCard} swipe={swipe} details={() => card && setSelected(card)} filters={() => navigate("statistics")} />}{tab === "matches" && <MatchesPage items={matches} loading={loading} error="" retry={loadMatches} select={openPlayer} />}{tab === "profile" && <ProfilePage profile={profile} edit={() => setEditing(true)} settings={() => navigate("settings")} />}{tab === "statistics" && <StatisticsPage preferences={preferences} statistics={statistics} loading={loading} error="" save={async (value) => { const saved = await endpoints.updatePreferences(value); setPreferences(saved); await loadCard(); }} />}{tab === "settings" && <SettingsPage connected onError={setError} />}</AppLayout>;
}
