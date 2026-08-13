import type { GameId, Party, PartyRequest, UserProfile } from "../types/api";

export const demoUser: UserProfile = { id: 1, user_id: 1, display_name: "Demo Player", avatar_url: "/assets/tactical-operator.png", birth_year: 2000, country_code: "EU", bio: "Clear comms. Ready to play.", languages: ["en"], microphone: true, playstyle: "Balanced", preferred_schedule: null, faceit_connected: false };
export function demoParties(game: GameId): Party[] { return [
  { id: 101, owner_user_id: 2, game, title: game === "valorant" ? "Premier evening stack" : game === "standoff2" ? "Competitive squad" : "Late night Premier", mode: game === "cs2" ? "Premier" : "Competitive", capacity: 5, current_members: 3, free_slots: 2, vibe: 68, language: "en", mic_required: true, rank_min: null, rank_max: null, description: "Two focused games. Calm comms and team play.", status: "OPEN", created_at: new Date().toISOString(), expires_at: new Date(Date.now()+21600000).toISOString(), request_status: null, members: [2,3,4].map((id,index)=>({user_id:id,display_name:`Player ${index+1}`,avatar_url:"/assets/tactical-operator.png",role:index?"MEMBER":"OWNER"})) },
]; }
export const demoRequests: PartyRequest[] = [{id:501,party_id:101,party_title:"Late night Premier",requester_user_id:7,requester_name:"a1rtek",status:"PENDING",created_at:new Date().toISOString()}];
