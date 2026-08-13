import type { Statistics } from "../../types/api";

function display(value: number | null, suffix = "", digits = 0) { return value == null || !Number.isFinite(value) ? "—" : `${value.toFixed(digits)}${suffix}`; }
export function StatGrid({ data, compact = false }: { data: Statistics; compact?: boolean }) {
  const all = [
    ["ELO", display(data.elo)], ["K/D", display(data.kd_ratio, "", 2)], ["ADR", display(data.adr, "", 1)],
    ["HS%", display(data.hs_percent, "%")], ["Победы", display(data.win_rate, "%")], ["Матчи", display(data.matches)],
  ];
  const items = compact ? all.slice(0, 3) : all;
  return <div className={`stat-grid ${compact ? "compact" : ""}`}>{items.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>;
}
