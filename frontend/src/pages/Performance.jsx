import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, Legend
} from "recharts";

export default function Performance() {
  const [summary, setSummary] = useState(null);
  const [byLeague, setByLeague] = useState([]);
  const [timeline, setTimeline] = useState([]);

  useEffect(() => {
    api.get("/performance/summary").then((r) => setSummary(r.data));
    api.get("/performance/by-league").then((r) => setByLeague(r.data));
    api.get("/performance/timeline").then((r) => setTimeline(r.data));
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-5 py-8" data-testid="performance-page">
        <div className="mb-8">
          <div className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-1.5">Performance tracking</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black uppercase tracking-tighter">Receipts</h1>
          <p className="text-sm text-zinc-400 mt-2 max-w-xl">Every prediction settled. Every dollar tracked. Flat $100 unit, -110 odds.</p>
        </div>

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10" data-testid="performance-summary">
            <BigStat label="Accuracy" value={`${summary.accuracy}%`} />
            <BigStat label="ROI" value={`${summary.roi >= 0 ? "+" : ""}${summary.roi}%`} accent={summary.roi >= 0 ? "win" : "loss"} />
            <BigStat label="Wins" value={summary.wins} />
            <BigStat label="Settled" value={summary.total_predictions} />
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-3">Cumulative profit · 21 days</div>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <LineChart data={timeline}>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#71717a" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                  <YAxis stroke="#71717a" fontSize={10} />
                  <Tooltip contentStyle={{ background: "#0a0a0b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, color: "#fff" }} />
                  <Line type="monotone" dataKey="cumulative_profit" stroke="#ff3b30" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-3">Accuracy by league</div>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={byLeague}>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="league_name" stroke="#71717a" fontSize={9} angle={-25} textAnchor="end" height={70} interval={0} />
                  <YAxis stroke="#71717a" fontSize={10} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: "#0a0a0b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, color: "#fff" }} />
                  <Bar dataKey="accuracy" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="mt-10 rounded-lg border border-white/10 bg-[#121214] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/10 text-[10px] uppercase tracking-[0.18em] text-zinc-500">Daily breakdown</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 bg-black/30">
                <tr>
                  <th className="text-left px-4 py-2.5">Date</th>
                  <th className="text-right px-4 py-2.5">Picks</th>
                  <th className="text-right px-4 py-2.5">Wins</th>
                  <th className="text-right px-4 py-2.5">Accuracy</th>
                  <th className="text-right px-4 py-2.5">Profit</th>
                  <th className="text-right px-4 py-2.5">Cumulative</th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((r) => (
                  <tr key={r.date} className="border-t border-white/5 tabular">
                    <td className="px-4 py-2.5 text-zinc-300">{r.date}</td>
                    <td className="px-4 py-2.5 text-right text-white">{r.total}</td>
                    <td className="px-4 py-2.5 text-right text-emerald-300">{r.wins}</td>
                    <td className="px-4 py-2.5 text-right text-white">{r.accuracy}%</td>
                    <td className={`px-4 py-2.5 text-right ${r.profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {r.profit >= 0 ? "+" : ""}${r.profit}
                    </td>
                    <td className={`px-4 py-2.5 text-right font-bold ${r.cumulative_profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {r.cumulative_profit >= 0 ? "+" : ""}${r.cumulative_profit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function BigStat({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
      <div className={`font-num text-5xl tabular ${accent === "win" ? "text-emerald-400" : accent === "loss" ? "text-red-400" : "text-white"}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mt-1">{label}</div>
    </div>
  );
}
