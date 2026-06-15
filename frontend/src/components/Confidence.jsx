export function ConfidenceBadge({ confidence, tier }) {
  const t = tier || (confidence >= 90 ? "90-95" : confidence >= 85 ? "85-89" : confidence >= 80 ? "80-84" : confidence >= 75 ? "75-79" : "below-75");
  const classes = {
    "90-95": "chip-elite",
    "85-89": "bg-emerald-500/10 text-emerald-300 border border-emerald-400/30",
    "80-84": "bg-sky-500/10 text-sky-300 border border-sky-400/30",
    "75-79": "bg-zinc-500/10 text-zinc-300 border border-zinc-400/20",
    "below-75": "bg-zinc-700/30 text-zinc-400 border border-zinc-500/20",
  }[t];
  return (
    <span
      data-testid={`confidence-badge-${t}`}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-bold tracking-[0.18em] uppercase ${classes}`}
    >
      <span className="font-num text-[14px] tracking-normal">{confidence}</span>
      <span>CONF</span>
    </span>
  );
}

export function WinBar({ homePct, awayPct, locked }) {
  if (locked || homePct == null) {
    return (
      <div className="bar-track">
        <div className="bar-fill bg-zinc-700/40 w-1/2" />
      </div>
    );
  }
  const hp = Math.round((homePct || 0) * 100);
  const ap = 100 - hp;
  return (
    <div className="flex items-center gap-2">
      <span className="font-num text-lg w-9 text-right text-white">{hp}</span>
      <div className="flex-1 bar-track flex">
        <div className="bar-fill" style={{ width: `${hp}%`, background: "#10b981" }} />
        <div className="bar-fill" style={{ width: `${ap}%`, background: "#ef4444" }} />
      </div>
      <span className="font-num text-lg w-9 text-zinc-300">{ap}</span>
    </div>
  );
}
