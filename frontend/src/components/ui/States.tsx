import { AlertCircle, RefreshCw, SearchX } from "lucide-react";

export function Skeleton({ tall = false }: { tall?: boolean }) { return <div className={`skeleton ${tall ? "skeleton-tall" : ""}`} aria-label="Загрузка" />; }
export function EmptyState({ title, text }: { title: string; text: string }) { return <section className="state"><SearchX aria-hidden /><h2>{title}</h2><p>{text}</p></section>; }
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) { return <section className="state error-state" role="alert"><AlertCircle aria-hidden /><h2>Что-то пошло не так</h2><p>{message}</p>{retry && <button className="button secondary" onClick={retry}><RefreshCw size={17} />Повторить</button>}</section>; }
export function Toast({ message, close }: { message: string; close: () => void }) { return <button className="toast" onClick={close} role="alert"><AlertCircle size={18} /><span>{message}</span></button>; }
