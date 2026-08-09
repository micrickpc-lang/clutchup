import axios from 'axios'
import { retrieveRawInitData } from '@telegram-apps/sdk'
function telegramInitData():string{try{return retrieveRawInitData()??''}catch{return''}}
export const api=axios.create({baseURL:'/api',timeout:15000})
api.interceptors.request.use((config)=>{config.headers.set('X-Telegram-Init-Data',telegramInitData());return config})
export type PlayerCardData={user_id:number;telegram_username:string|null;display_name:string;faceit_nickname:string;avatar_url:string|null;elo:number;skill_level:number;kd_ratio:number;role:string;bio:string}
export type Profile={faceit_nickname:string;avatar_url:string|null;elo:number;skill_level:number;kd_ratio:number;role:string;bio:string;is_searching:boolean}
