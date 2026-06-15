import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { ConfidenceBadge, WinBar } from "@/components/Confidence";
import { Lock, ShieldCheck, TrendingUp } from "lucide-react";

export default function MatchDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get(`/predictions/${id}`).then((r) => setData(r.data)).catch(() => {});
  }, [id]);

  if (!data) return <Layout><div className="max-w-5xl mx-auto px-5 py-16 text-zinc-500">Loading…</div></Layout>;
  const { game, prediction } = data;
  const home = game?.home_team;
  const away = game?.away_team;
  const locked = prediction?.locked;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-5 py-8 fade-in" data-testid="match-detail">
        <div className="mb-2 text-[10px] uppercase tracking-[0.25em] text-zinc-500">
          <Link to="/matches" className="hover:text-white">Match Center</Link> · {game?.league?.name}
        </div>
        <div className="rounded-lg border border-white/10 bg-[#121214] p-6 mb-6">
          <div className="grid grid-cols-[1fr_auto_1fr] gap-6 items-center mb-6">
            <div>
              <div className="text-xs text-zinc-500 uppercase tracking-[0.18em]">Home</div>
              <div className="font-display text-3xl text-white">{home?.name}</div>
              <div className="text-xs text-zinc-400">{home?.city}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-zinc-500 uppercase tracking-[0.18em]">Tip-off</div>
              <div className="font-num text-2xl text-white tabular">
                {new Date(game?.start_time).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
              </div>
              <div className="text-xs text-zinc-500 mt-1">{game?.venue}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-zinc-500 uppercase tracking-[0.18em]">Away</div>
              <div className="font-display text-3xl text-white">{away?.name}</div>
              <div className="text-xs text-zinc-400">{away?.city}</div>
            </div>
          </div>

          <div className="mb-6">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Win probability</div>
            <WinBar homePct={prediction?.home_win_prob} awayPct={prediction?.away_win_prob} locked={locked} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KV label="Confidence" value={<ConfidenceBadge confidence={prediction?.confidence} tier={prediction?.confidence_tier} />} />
            <KV label="Spread" value={locked ? "—" : (prediction?.predicted_spread > 0 ? "+" : "") + prediction?.predicted_spread} />
            <KV label="Total" value={locked ? "—" : prediction?.predicted_total} />
            <KV label="Market line" value={locked ? "—" : `${prediction?.market_spread} / ${prediction?.market_total}`} />
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            {prediction?.is_value_bet && (
              <span className="inline-flex items-center gap-1 text-amber-300 text-[11px] uppercase tracking-[0.15em] font-bold px-2 py-1 rounded border border-amber-400/30">
                <TrendingUp size={12} /> Value Bet
              </span>
            )}
            {prediction?.is_safest_pick && (
              <span className="inline-flex items-center gap-1 text-emerald-300 text-[11px] uppercase tracking-[0.15em] font-bold px-2 py-1 rounded border border-emerald-400/30">
                <ShieldCheck size={12} /> Safest Pick
              </span>
            )}
            {locked && (
              <Link
                to="/pricing"
                className="inline-flex items-center gap-1 text-amber-300 text-[11px] uppercase tracking-[0.15em] font-bold px-2 py-1 rounded border border-amber-400/30 hover:bg-amber-400/10"
              >
                <Lock size={12} /> Premium — Unlock
              </Link>
            )}
          </div>
        </div>

        {/* Period breakdown */}
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-3">First Quarter Winner</div>
            <WinBar homePct={prediction?.first_quarter_home_prob} awayPct={1 - (prediction?.first_quarter_home_prob || 0)} locked={locked} />
          </div>
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-3">First Half Winner</div>
            <WinBar homePct={prediction?.first_half_home_prob} awayPct={1 - (prediction?.first_half_home_prob || 0)} locked={locked} />
          </div>
        </div>

        {/* Predicted score */}
        <div className="rounded-lg border border-white/10 bg-[#121214] p-5 mb-6">
          <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Predicted final</div>
          <div className="grid grid-cols-3 items-center text-center">
            <div className="font-num text-5xl tabular text-white">{prediction?.predicted_home_score}</div>
            <div className="text-zinc-500 text-sm">vs</div>
            <div className="font-num text-5xl tabular text-zinc-300">{prediction?.predicted_away_score}</div>
          </div>
        </div>

        {/* Model breakdown */}
        {prediction?.model_breakdown && !locked && (
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">Model breakdown — home win probability per signal</div>
              {prediction.engine && (
                <span className={`text-[10px] uppercase tracking-[0.18em] font-bold ${prediction.engine === "ensemble-ml" ? "text-emerald-300" : "text-zinc-400"}`}>
                  {prediction.engine === "ensemble-ml" ? "XGBoost + LightGBM Ensemble" : "Statistical Engine"}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(prediction.model_breakdown).map(([k, v]) => (
                <KV key={k} label={k} value={`${Math.round(v * 100)}%`} />
              ))}
            </div>
            {prediction.adjustments && Object.keys(prediction.adjustments).length > 0 && (
              <>
                <div className="mt-4 text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Adjustments</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {Object.entries(prediction.adjustments).map(([k, v]) => (
                    <KV key={k} label={k.replace("_", " ")} value={v > 0 ? `+${(v * 100).toFixed(1)}%` : `${(v * 100).toFixed(1)}%`} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Team strengths */}
        <div className="grid md:grid-cols-2 gap-4">
          <TeamStrengths team={home} label="Home" />
          <TeamStrengths team={away} label="Away" />
        </div>

        <p className="mt-10 text-[11px] text-center text-zinc-500">
          Predictions are <span className="text-amber-300">statistical estimates</span> and not guaranteed outcomes.
        </p>
      </div>
    </Layout>
  );
}

function KV({ label, value }) {
  return (
    <div className="rounded border border-white/5 bg-black/30 p-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</div>
      <div className="text-white text-sm font-bold mt-1 capitalize tabular">{value}</div>
    </div>
  );
}

function TeamStrengths({ team, label }) {
  if (!team) return null;
  return (
    <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
      <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">{label} · {team.name}</div>
      <div className="grid grid-cols-2 gap-3">
        <KV label="Off Rtg" value={team.off_rating?.toFixed(1)} />
        <KV label="Def Rtg" value={team.def_rating?.toFixed(1)} />
        <KV label="Pace" value={team.pace?.toFixed(1)} />
        <KV label="Elo" value={team.elo} />
        <KV label="Last 5" value={team.form} />
        <KV label="Injuries" value={team.injuries ?? 0} />
      </div>
    </div>
  );
}
