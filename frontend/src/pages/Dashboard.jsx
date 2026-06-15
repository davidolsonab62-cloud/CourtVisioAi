import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { PredictionCard, LiveGameCard } from "@/components/Cards";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Crown, Flame, ShieldCheck } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [live, setLive] = useState([]);
  const [today, setToday] = useState([]);
  const [trending, setTrending] = useState([]);
  const [premium, setPremium] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get("/games/live").then((r) => setLive(r.data)).catch(() => {});
    api.get("/predictions/today").then((r) => setToday(r.data)).catch(() => {});
    api.get("/predictions/trending").then((r) => setTrending(r.data)).catch(() => {});
    api.get("/predictions/premium").then((r) => setPremium(r.data)).catch(() => {});
    api.get("/performance/summary").then((r) => setSummary(r.data)).catch(() => {});
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-5 py-8" data-testid="dashboard">
        {/* Headline strip */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-1.5">Today / {new Date().toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}</div>
            <h1 className="font-display text-4xl sm:text-5xl font-black uppercase tracking-tighter">Control room</h1>
          </div>
          {summary && (
            <div className="grid grid-cols-4 gap-4">
              <Stat label="Acc 21d" value={`${summary.accuracy}%`} />
              <Stat label="ROI 21d" value={`+${summary.roi}%`} accent="win" />
              <Stat label="Wins" value={summary.wins} />
              <Stat label="Losses" value={summary.losses} />
            </div>
          )}
        </div>

        {/* Live ribbon */}
        {live.length > 0 && (
          <section className="mb-10">
            <SectionHeader icon={Activity} title="Live now" count={live.length} />
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {live.map((g) => <LiveGameCard key={g.id} game={g} />)}
            </div>
          </section>
        )}

        {/* Today's predictions */}
        <section className="mb-10" data-testid="todays-predictions">
          <SectionHeader icon={ArrowRight} title="Today's predictions" count={today.length} />
          {today.length === 0 ? (
            <Empty text="No high-confidence picks for the next 24h. Check back soon." />
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {today.slice(0, 9).map(({ game, prediction }) => (
                <PredictionCard key={game.id} game={game} prediction={prediction} />
              ))}
            </div>
          )}
        </section>

        {/* Trending value bets */}
        <section className="mb-10">
          <SectionHeader icon={Flame} title="Trending value" count={trending.length} subtitle="Edges our model spots vs the market" />
          {trending.length === 0 ? (
            <Empty text="No outsized value spotted right now." />
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {trending.map(({ game, prediction }) => (
                <PredictionCard key={game.id} game={game} prediction={prediction} />
              ))}
            </div>
          )}
        </section>

        {/* Premium picks */}
        <section className="mb-10">
          <SectionHeader icon={Crown} title="Premium 88+ picks" count={premium.length} />
          {!user?.is_premium ? (
            <div className="rounded-lg border border-amber-400/30 bg-amber-500/5 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="font-display text-xl text-white">Premium picks are locked</div>
                <p className="text-sm text-zinc-400 mt-1">Upgrade to see every 88-99 confidence pick across the globe.</p>
              </div>
              <Link
                data-testid="dashboard-upgrade-btn"
                to="/pricing"
                className="bg-[#ff3b30] hover:bg-[#dc2626] text-white px-5 py-3 rounded font-bold uppercase tracking-widest text-sm"
              >
                Upgrade
              </Link>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {premium.map(({ game, prediction }) => (
                <PredictionCard key={game.id} game={game} prediction={prediction} />
              ))}
            </div>
          )}
        </section>

        <p className="mt-12 text-[11px] text-center text-zinc-500">
          Predictions are <span className="text-amber-300">statistical estimates</span> and not guaranteed outcomes.
        </p>
      </div>
    </Layout>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div className="border-l border-white/10 pl-3">
      <div className={`font-num text-2xl tabular ${accent === "win" ? "text-emerald-400" : "text-white"}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</div>
    </div>
  );
}

function SectionHeader({ icon: Icon, title, count, subtitle }) {
  return (
    <div className="flex items-end justify-between mb-4">
      <div>
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-[#ff3b30]" />
          <h2 className="font-display text-2xl font-bold uppercase tracking-tight">{title}</h2>
          {count != null && (
            <span className="text-[10px] tracking-[0.18em] uppercase text-zinc-500 ml-2 font-bold">{count}</span>
          )}
        </div>
        {subtitle && <div className="text-xs text-zinc-500 mt-1">{subtitle}</div>}
      </div>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="border border-dashed border-white/10 rounded-lg p-8 text-center text-sm text-zinc-500">
      {text}
    </div>
  );
}
