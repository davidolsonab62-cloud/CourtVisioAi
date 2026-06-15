import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Crown, Heart, Bell } from "lucide-react";

export default function Profile() {
  const { user, refreshMe } = useAuth();
  const [teams, setTeams] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [favs, setFavs] = useState([]);

  useEffect(() => {
    if (user) {
      setFavs(user.favorites || []);
      api.get("/teams").then((r) => setTeams(r.data));
      api.get("/me/notifications").then((r) => setNotifications(r.data));
    }
  }, [user]);

  const toggleFavorite = async (team_id) => {
    if (favs.includes(team_id)) {
      await api.delete(`/me/favorites/${team_id}`);
      setFavs(favs.filter((id) => id !== team_id));
    } else {
      await api.post("/me/favorites", { team_id });
      setFavs([...favs, team_id]);
    }
    refreshMe();
  };

  if (!user) {
    return <Layout><div className="max-w-3xl mx-auto px-5 py-16 text-zinc-500">Loading…</div></Layout>;
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-5 py-8" data-testid="profile-page">
        <div className="mb-8">
          <div className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-1.5">Account</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black uppercase tracking-tighter">{user.name}</h1>
          <p className="text-sm text-zinc-400 mt-2">{user.email}</p>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-10">
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Subscription</div>
            <div className={`font-display text-2xl ${user.is_premium ? "text-amber-300" : "text-zinc-300"}`}>
              {user.is_premium ? <span className="flex items-center gap-2"><Crown size={18} /> Premium</span> : "Free"}
            </div>
            {user.premium_until && (
              <div className="text-xs text-zinc-500 mt-1">Until {new Date(user.premium_until).toLocaleDateString()}</div>
            )}
          </div>
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Favorites</div>
            <div className="font-num text-3xl tabular text-white">{favs.length}</div>
          </div>
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-2">Member since</div>
            <div className="font-display text-base text-white">{new Date(user.created_at).toLocaleDateString()}</div>
          </div>
        </div>

        <section className="mb-10">
          <div className="flex items-center gap-2 mb-3"><Bell size={14} className="text-[#ff3b30]" /><h2 className="font-display text-2xl uppercase tracking-tight">Notifications</h2></div>
          <div className="rounded-lg border border-white/10 bg-[#121214] divide-y divide-white/5">
            {notifications.map((n) => (
              <div key={n.id} className="px-4 py-3 flex items-start justify-between gap-3">
                <div>
                  <div className="text-white text-sm font-bold">{n.title}</div>
                  <div className="text-xs text-zinc-400 mt-0.5">{n.body}</div>
                </div>
                <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 shrink-0">{new Date(n.created_at).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <div className="flex items-center gap-2 mb-3"><Heart size={14} className="text-[#ff3b30]" /><h2 className="font-display text-2xl uppercase tracking-tight">Favorite teams</h2></div>
          <div className="flex flex-wrap gap-2">
            {teams.map((t) => {
              const active = favs.includes(t.id);
              return (
                <button
                  key={t.id}
                  data-testid={`team-fav-${t.id}`}
                  onClick={() => toggleFavorite(t.id)}
                  className={`px-3 py-1.5 rounded text-xs font-bold uppercase tracking-widest border transition-colors ${active ? "bg-[#ff3b30] text-white border-[#ff3b30]" : "text-zinc-300 border-white/10 hover:border-white/30"}`}
                >
                  {t.short} · {t.name}
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </Layout>
  );
}
