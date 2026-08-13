import { useEffect } from "react";
import { AppProvider,useApp } from "./app/AppProvider";
import { ProductShell } from "./components/layout/ProductShell";
import { LocaleProvider,useLocale } from "./i18n/LocaleProvider";
function RegionLocaleSync(){const {user}=useApp(),{applyCountry}=useLocale();useEffect(()=>applyCountry(user?.country_code||null),[user?.country_code,applyCountry]);return null}
export default function App(){return <LocaleProvider><AppProvider><RegionLocaleSync/><ProductShell/></AppProvider></LocaleProvider>}
