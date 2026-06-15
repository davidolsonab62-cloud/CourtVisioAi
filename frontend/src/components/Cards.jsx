import { Link } from "react-router-dom";
import { Lock, TrendingUp, ShieldCheck, Sparkles } from "lucide-react";
import { ConfidenceBadge, WinBar } from "@/components/Confidence";

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" });
}

export function PredictionCard({ game, prediction, compact }) {
  if (!game) return null;
  const home = game.home_team;
  const away = game.away_team;
  const locked = prediction?.locked;
  const winnerIsHome = prediction && prediction.predicted_winner_id === home?.id;
  const spread = prediction?.predicted_spread;
  const total = prediction?.predicted_total;

  return (
    <Link
      to={`/match/${game.id}`}
      data-testid={`prediction-card-${game.id}`}
      className="card-hover block rounded-lg border border-white/10 bg-[#121214] p-4"
    >
      <div className="flex items-center justify-between text-[10px] tracking-[0.18em] uppercase text-zinc-500 mb-3">
        <span className="flex items-center gap-2">
          <span>{game.league?.name || game.league_id}</span>
          {game.status === "live" && (
            <span className="flex items-center gap-1.5 text-red-400 font-bold">
              <span className="live-dot" /> LIVE
            </span>
          )}
        </span>
        <span className="tabular text-zinc-400">{formatTime(game.start_time)}</span>
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] gap-3 items-center mb-4">
        <div className="text-left">
          <div className="font-display text-lg leading-tight text-white truncate">{home?.short}</div>
          <div className="text-xs text-zinc-400 truncate">{home?.name}</div>
        </div>
        <div className="text-zinc-500 text-xs font-bold">@</div>
        <div className="text-right">
          <div className="font-display text-lg leading-tight text-white truncate">{away?.short}</div>
          <div className="text-xs text-zinc-400 truncate">{away?.name}</div>
        </div>
      </div>

      {prediction && (
        <>
          <WinBar homePct={prediction.home_win_prob} awayPct={prediction.away_win_prob} locked={locked} />

          {!compact && (
            <div className="grid grid-cols-3 gap-2 mt-4 text-center">
              <div className="rounded border border-white/5 bg-black/30 py-2">
                <div className="text-[9px] tracking-[0.18em] text-zinc-500">WINNER</div>
                <div className="font-display text-sm text-white mt-0.5">
                  {locked ? "—" : winnerIsHome ? home?.short : away?.short}
                </div>
              </div>
              <div className="rounded border border-white/5 bg-black/30 py-2">
                <div className="text-[9px] tracking-[0.18em] text-zinc-500">SPREAD</div>
                <div className="font-num text-base text-white mt-0.5 tabular">
                  {locked ? "—" : spread > 0 ? `+${spread}` : spread}
                </div>
              </div>
              <div className="rounded border border-white/5 bg-black/30 py-2">
                <div className="text-[9px] tracking-[0.18em] text-zinc-500">TOTAL</div>
                <div className="font-num text-base text-white mt-0.5 tabular">
                  {locked ? "—" : total}
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-4">
            <ConfidenceBadge confidence={prediction.confidence} tier={prediction.confidence_tier} />
            <div className="flex items-center gap-1.5">
              {prediction.is_value_bet && (
                <span data-testid="value-bet-badge" className="inline-flex items-center gap-1 text-amber-300 text-[10px] uppercase tracking-[0.15em] font-bold">
                  <TrendingUp size={12} /> Value
                </span>
              )}
              {prediction.is_safest_pick && (
                <span data-testid="safest-pick-badge" className="inline-flex items-center gap-1 text-emerald-300 text-[10px] uppercase tracking-[0.15em] font-bold">
                  <ShieldCheck size={12} /> Safest
                </span>
              )}
              {locked && (
                <span className="inline-flex items-center gap-1 text-amber-300 text-[10px] uppercase tracking-[0.15em] font-bold">
                  <Lock size={12} /> Premium
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </Link>
  );
}

export function LiveGameCard({ game }) {
  if (!game) return null;
  return (
    <div data-testid={`live-game-${game.id}`} className="rounded-lg border border-red-500/30 bg-[#121214] p-4">
      <div className="flex items-center justify-between mb-3 text-[10px] tracking-[0.18em] uppercase">
        <span className="text-zinc-400">{game.league?.name || game.league_id}</span>
        <span className="flex items-center gap-1.5 text-red-400 font-bold">
          <span className="live-dot" /> {game.current_period || "LIVE"}
        </span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div className="text-left">
          <div className="text-xs text-zinc-400 truncate">{game.home_team?.short}</div>
          <div className="font-num text-4xl text-white tabular">{game.home_score ?? "—"}</div>
        </div>
        <div className="text-zinc-600 font-display text-sm">VS</div>
        <div className="text-right">
          <div className="text-xs text-zinc-400 truncate">{game.away_team?.short}</div>
          <div className="font-num text-4xl text-white tabular">{game.away_score ?? "—"}</div>
        </div>
      </div>
    </div>
  );
}
