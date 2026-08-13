import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { endpoints, errorMessage } from "../api/client";
import { GAME_CONFIG } from "../config/games";
import { demoParties, demoRequests, demoUser } from "./demoFixtures";
import type { AppTab, DiscoverFilters, GameId, GameProfile, Party, PartyCreate, PartyRequest, UserProfile } from "../types/api";

type State = {
  tab: AppTab; setTab: (value: AppTab) => void;
  user: UserProfile | null; game: GameId; setGame: (value: GameId) => void;
  gameProfile: GameProfile | null; gameProfiles: GameProfile[]; parties: Party[]; mine: Party[]; requests: PartyRequest[];
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
  const requestId = useRef(0);
  const joining = useRef(new Set<number>());
  const deciding = useRef(new Set<number>());

  const setGame = useCallback((value: GameId) => {
    localStorage.setItem("clutchup.game", value);
    setGameState(value);
    setFilters({ ...defaults, mode: GAME_CONFIG[value].modes[0] });
  }, []);
  const reload = useCallback(async () => {
    const currentRequest = ++requestId.current;
    setLoading(true); setError("");
    if (demo) {
      setUser(demoUser); setProfiles([]); setParties(demoParties(game)); setMine([]); setRequests(demoRequests); setLoading(false); return;
    }
    try {
      const params = { mode: filters.mode || undefined, free_slots: filters.freeSlots, language: filters.language || undefined, mic_required: filters.micRequired ?? undefined };
      const [me, gameProfiles, feed, own, inbox] = await Promise.all([endpoints.me(), endpoints.gameProfiles(), endpoints.discoverParties(game, params), endpoints.myParties(), endpoints.partyRequests()]);
      if(currentRequest!==requestId.current)return;
      setUser(me); setProfiles(gameProfiles); setParties(feed); setMine(own); setRequests(inbox);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { if(currentRequest===requestId.current)setLoading(false); }
  }, [demo, game, filters]);
  useEffect(() => { void reload(); }, [reload]);
  const join = useCallback(async (id: number) => {
    if(joining.current.has(id))return;
    joining.current.add(id);
    setParties(value => value.map(party => party.id === id ? { ...party, request_status: "PENDING" } : party));
    if (demo) { joining.current.delete(id); return; }
    try { await endpoints.requestParty(id); await reload(); }
    catch (reason) { setParties(value => value.map(party => party.id === id ? { ...party, request_status: null } : party)); setError(errorMessage(reason)); throw reason; }
    finally { joining.current.delete(id); }
  }, [demo, reload]);
  const create = useCallback(async (data: PartyCreate) => { if(demo){const created:Party={...data,id:Date.now(),owner_user_id:demoUser.user_id,current_members:1,free_slots:data.capacity-1,status:"OPEN",created_at:new Date().toISOString(),expires_at:new Date(Date.now()+21600000).toISOString(),members:[{user_id:demoUser.user_id,display_name:demoUser.display_name,avatar_url:demoUser.avatar_url,role:"OWNER"}],request_status:null};setMine(value=>[created,...value]);setTab("parties");return}await endpoints.createParty(data);setTab("parties");await reload(); }, [demo, reload]);
  const decide = useCallback(async (id: number, accept: boolean) => {
    if(deciding.current.has(id))return;
    deciding.current.add(id);
    const request=requests.find(item=>item.id===id);
    if(demo){if(accept&&request){const party=demoParties(game).find(item=>item.id===request.party_id);if(party)setPartyFound({...party,current_members:party.current_members+1,free_slots:Math.max(0,party.free_slots-1)})}setRequests(value=>value.map(item=>item.id===id?{...item,status:accept?"ACCEPTED":"REJECTED"}:item));deciding.current.delete(id);return}
    try{if(accept)await endpoints.acceptRequest(id);else await endpoints.rejectRequest(id);if(accept&&request)setPartyFound(await endpoints.party(request.party_id));await reload()}finally{deciding.current.delete(id)}
  }, [demo,game,reload, requests]);
  const clearPartyFound = useCallback(() => setPartyFound(null), []);
  const value = useMemo(() => ({ tab, setTab, user, game, setGame, gameProfile: profiles.find(profile => profile.game === game) || null, gameProfiles:profiles, parties, mine, requests, partyFound, clearPartyFound, filters, setFilters, loading, error, reload, join, create, decide }), [tab, user, game, setGame, profiles, parties, mine, requests, partyFound, clearPartyFound, filters, loading, error, reload, join, create, decide]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useApp() { const value = useContext(Context); if (!value) throw new Error("AppProvider missing"); return value; }
