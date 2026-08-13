import { useState } from "react";
import { useApp } from "../../app/AppProvider";
import { GAME_CONFIG } from "../../config/games";
import type { PartyCreate } from "../../types/api";
import { Sheet } from "../ui/Sheet";
import styles from "./CreatePartySheet.module.css";

const vibes = [[25, "CHILL"], [50, "BALANCED"], [80, "TRYHARD"]] as const;

export function CreatePartySheet({ close }: { close: () => void }) {
  const { game, create } = useApp();
  const config = GAME_CONFIG[game];
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<PartyCreate>({
    game, title: "", mode: config.modes[0], capacity: config.maxPartySize,
    vibe: 50, language: null, mic_required: false, rank_min: null,
    rank_max: null, description: "",
  });

  return <Sheet title="CREATE PARTY" close={close}>
    <form className={styles.form} onSubmit={async event => {
      event.preventDefault();
      if (busy) return;
      setBusy(true);
      try { await create(data); close(); } finally { setBusy(false); }
    }}>
      <label>TITLE<input required maxLength={80} value={data.title} onChange={event => setData({ ...data, title: event.target.value })} placeholder="Late night stack" /></label>
      <div>
        <label>MODE<select value={data.mode} onChange={event => setData({ ...data, mode: event.target.value })}>{config.modes.map(mode => <option key={mode}>{mode}</option>)}</select></label>
        <label>CAPACITY<input type="number" min="2" max={config.maxPartySize} value={data.capacity} onChange={event => setData({ ...data, capacity: +event.target.value })} /></label>
      </div>
      <label>VIBE<div className={styles.vibe}>{vibes.map(([value, label]) => <button type="button" key={value} className={data.vibe === value ? styles.active : ""} onClick={() => setData({ ...data, vibe: value })}>{label}</button>)}</div></label>
      <label>LANGUAGE<input maxLength={16} value={data.language || ""} onChange={event => setData({ ...data, language: event.target.value || null })} placeholder="EN" /></label>
      <label className={styles.check}><input type="checkbox" checked={data.mic_required} onChange={event => setData({ ...data, mic_required: event.target.checked })} /> MIC REQUIRED</label>
      <label>DESCRIPTION<textarea maxLength={500} value={data.description} onChange={event => setData({ ...data, description: event.target.value })} /></label>
      <button className="primary-action" disabled={busy}>{busy ? "CREATING..." : "CREATE PARTY"}</button>
    </form>
  </Sheet>;
}
