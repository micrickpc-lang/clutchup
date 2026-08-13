import { Bell, ExternalLink, Info, Languages, Link2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { endpoints, errorMessage } from "../../api/client";
import { PageHeader } from "../../components/layout/AppLayout";
import { openExternal } from "../../lib/telegram";

export function SettingsPage({ connected, onError }: { connected: boolean; onError: (message: string) => void }) {
  const [busy, setBusy] = useState(false);
  const connect = async () => { setBusy(true); try { const { authorization_url } = await endpoints.oauthStart(); openExternal(authorization_url); } catch (error) { onError(errorMessage(error)); } finally { setBusy(false); } };
  return <><PageHeader title="Настройки" /><section className="page-body settings"><div className="panel settings-list"><p><Bell /><span>Уведомления</span><small>Telegram</small></p><p><Languages /><span>Язык приложения</span><small>Русский</small></p><button onClick={() => openExternal("https://t.me/ClutchUp_bot")}><ExternalLink /><span>Открыть в Telegram</span></button></div><button className={`faceit-connect ${connected ? "connected" : ""}`} disabled={busy} onClick={connect}><Link2 />{busy ? "Открываем FACEIT…" : connected ? "Переподключить FACEIT" : "Подключить FACEIT аккаунт"}</button><p className="security-note"><ShieldCheck />Пароль вводится только на accounts.faceit.com</p><div className="panel settings-list"><p><Info /><span>О приложении</span><small>ClutchUp v2.0.0</small></p></div></section></>;
}
