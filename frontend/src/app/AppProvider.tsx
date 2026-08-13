import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { endpoints, errorMessage } from "../api/client";
import { GAME_CONFIG } from "../config/games";
import { demoParties, demoRequests, demoUser } from "./demoFixtures";
import type { AppTab, DiscoverFilters, GameId, GameProfile, Party, PartyCreate, PartyRequest, UserProfile } from "../types/api";

type State = {
  tab: AppTab; setTab: (value: AppTab) => void;
  user: UserProfile | null; game: GameId; setGame: (value: GameId) => void;
  gameProfile: GameProfile | null; parties: Party[]; mine: Party[]; requests: PartyRequest[];
  partyFound: Party | null; clearPartyFound: () => void;
  filters: DiscoverFilters; setFilters: (value: DiscoverFilters) => void;
  loading: boolean; error: string; reload: () => Promise<void>;
  join: (id: number) => Promise<void>; create: (data: PartyCreate) => Promise<void>;
  decide: (id: number, accept: boolean) => Promise<void>;
};
const Context = createContext<State | null>(null);
const defaults: DiscoverFilters = { mode: null, freeSlots: 1, vibe: 50, language: null, micRequired: null };

export function AppProvider({ children }: { children: ReactNode }) {
  const demo = import.meta.env.DEV && new URLSearchParams(location.search).get("demo") === "1";
  const [tab, setTab] = useState<AppTab>("find");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [game, setGameState] = useState<GameId>(() => (localStorage.getItem("clutchup.game") as GameId) || "cs2");
  const [profiles, setProfiles] = useState<GameProfile[]>([]);
  const [parties, setParties] = useState<Party[]>([]);
  const [mine, setMine] = useState<Party[]>([]);
  const [requests, setRequests] = useState<PartyRequest[]>([]);
  const [filters, setFilters] = useState(defaults);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [partyFound, setPartyFound] = useState<Party | null>(null);

  const setGame = useCallback((value: GameId) => {
    localStorage.setItem("clutchup.game", value);
    setGameState(value);
    setFilters({ ...defaults, mode: GAME_CONFIG[value].modes[0] });
  }, []);
  const reload = useCallback(async () => {
    setLoading(true); setError("");
    if (demo) {
      setUser(demoUser); setProfiles([]); setParties(demoParties(game)); setMine([]); setRequests(demoRequests); setLoading(false); return;
    }
    try {
      const params = { mode: filters.mode || undefined, free_slots: filters.freeSlots, language: filters.language || undefined, mic_required: filters.micRequired ?? undefined };
      const [me, gameProfiles, feed, own, inbox] = await Promise.all([endpoints.me(), endpoints.gameProfiles(), endpoints.discoverParties(game, params), endpoints.myParties(), endpoints.partyRequests()]);
      setUser(me); setProfiles(gameProfiles); setParties(feed); setMine(own); setRequests(inbox);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }, [demo, game, filters]);
  useEffect(() => { void reload(); }, [reload]);
  const join = useCallback(async (id: number) => {
    setParties(value => value.map(party => party.id === id ? { ...party, request_status: "PENDING" } : party));
    if (demo) return;
    try { await endpoints.requestParty(id); await reload(); }
    catch (reason) { setParties(value => value.map(party => party.id === id ? { ...party, request_status: null } : party)); setError(errorMessage(reason)); throw reason; }
  }, [demo, reload]);
  const create = useCallback(async (data: PartyCreate) => { if (!demo) await endpoints.createParty(data); setTab("parties"); await reload(); }, [demo, reload]);
  const decide = useCallback(async (id: number, accept: boolean) => {
    if (accept) await endpoints.acceptRequest(id); else await endpoints.rejectRequest(id);
    if (accept) {
      const request = requests.find(item => item.id === id);
      if (request) setPartyFound(await endpoints.party(request.party_id));
    }
    await reload();
  }, [reload, requests]);
  const clearPartyFound = useCallback(() => setPartyFound(null), []);
  const value = useMemo(() => ({ tab, setTab, user, game, setGame, gameProfile: profiles.find(profile => profile.game === game) || null, parties, mine, requests, partyFound, clearPartyFound, filters, setFilters, loading, error, reload, join, create, decide }), [tab, user, game, setGame, profiles, parties, mine, requests, partyFound, clearPartyFound, filters, loading, error, reload, join, create, decide]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useApp() { const value = useContext(Context); if (!value) throw new Error("AppProvider missing"); return value; }
