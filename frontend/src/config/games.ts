import type { GameId } from "../types/api";

export type GameConfig = { id:GameId; displayName:string; shortName:string; modes:string[]; maxPartySize:number; roles:string[]; rankSupport:boolean; integration?:"faceit"; tone:string };
export const GAME_CONFIG:Record<GameId,GameConfig>={
 cs2:{id:"cs2",displayName:"Counter-Strike 2",shortName:"CS2",modes:["Premier","Competitive","FACEIT"],maxPartySize:5,roles:["Rifler","AWPer","IGL","Support","Entry"],rankSupport:true,integration:"faceit",tone:"amber"},
 valorant:{id:"valorant",displayName:"VALORANT",shortName:"VALORANT",modes:["Competitive","Unrated","Premier"],maxPartySize:5,roles:["Duelist","Controller","Initiator","Sentinel"],rankSupport:true,tone:"crimson"},
 standoff2:{id:"standoff2",displayName:"Standoff 2",shortName:"STANDOFF 2",modes:["Competitive","Defuse","Team Deathmatch"],maxPartySize:5,roles:["Rifler","Sniper","Support","Entry"],rankSupport:true,tone:"orange"},
};
export const GAME_IDS=Object.keys(GAME_CONFIG) as GameId[];
