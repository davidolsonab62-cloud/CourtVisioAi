import { useEffect, useMemo, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { PredictionCard } from "@/components/Cards";

export default function MatchCenter() {
  const [leagues, setLeagues] = useState([]);
  const [selected, setSelected] = useState("all");
  const [today, setToday] = useState([]);

  useEffect(() => {
    api.get("/leagues").then((r) => setLeagues(r.data)).catch(() => {});
    api.get("/predictions/today").then((r) => setToday(r.data)).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    if (selected === "all") return today;
    return today.filter((row) => row.game?.league_id === selected);
  }, [today, selected]);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-5 py-8" data-testid="match-center">
        <div className="mb-6">
          <div className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-1.5">Daily match center</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black uppercase tracking-tighter">All Games · Next 36h</h1>
        </div>

        <div className="flex flex-wrap gap-2 mb-8 overflow-x-auto">
          <Chip active={selected === "all"} onClick={() => setSelected("all")} testId="league-chip-all">All</Chip>
          {leagues.map((l) => (
            <Chip key={l.id} active={selected === l.id} onClick={() => setSelected(l.id)} testId={`league-chip-${l.id}`}>
              <span className="mr-1">{l.logo}</span> {l.name}
            </Chip>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="border border-dashed border-white/10 rounded-lg p-10 text-center text-sm text-zinc-500">
            No matches found in this league right now.
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 fade-in">
            {filtered.map(({ game, prediction }) => (
              <PredictionCard key={game.id} game={game} prediction={prediction} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}

function Chip({ children, active, onClick, testId }) {
  return (
    <button
      data-testid={testId}
      onClick={onClick}
      className={`whitespace-nowrap px-3 py-1.5 rounded text-xs uppercase tracking-widest font-bold transition-colors border ${active ? "bg-[#ff3b30] text-white border-[#ff3b30]" : "bg-transparent text-zinc-300 border-white/10 hover:border-white/30"}`}
    >
      {children}
    </button>
  );
}
