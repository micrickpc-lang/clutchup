import { useApp } from "../app/AppProvider";
import { useLocale } from "../i18n/LocaleProvider";
import { InboxItem } from "../components/inbox/InboxItem";
import { EmptyState } from "../components/ui/EmptyState";
export function InboxPage(){const app=useApp(),{t}=useLocale();return <section className="page"><h1 className="page-title">{t("inbox")}</h1><p className="page-copy">{t("inboxCopy")}</p><div className="section-head"><h2>{t("activity")}</h2></div>{app.requests.length?<div style={{display:"grid",gap:10}}>{app.requests.map(r=><InboxItem key={r.id} request={r} own={r.requester_user_id===app.user?.user_id} decide={app.decide}/>)}</div>:<EmptyState title={t("inboxClear")} text={t("inboxClearText")}/>}</section>}
