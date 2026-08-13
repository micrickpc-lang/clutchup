import { Languages } from "lucide-react";
import { useLocale,type Locale } from "../../i18n/LocaleProvider";
import styles from "./LanguageSettings.module.css";
export function LanguageSettings(){const {locale,setLocale,t}=useLocale();return <section className={styles.language}><div><Languages/><span><strong>{t("appLanguage")}</strong><small>{t("autoRegion")}</small></span></div><div role="group" aria-label={t("appLanguage")}>{([["ru",t("russian")],["en",t("english")]] as [Locale,string][]).map(([id,label])=><button key={id} className={locale===id?styles.selected:""} onClick={()=>setLocale(id)} aria-pressed={locale===id}>{label}</button>)}</div></section>}
