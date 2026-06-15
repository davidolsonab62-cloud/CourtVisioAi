import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { Crown, Trash2, ShieldOff, Users, DollarSign, Activity, KeyRound, Brain, RefreshCw, Zap } from "lucide-react";

export default function Admin() {
  const [dash, setDash] = useState(null);
  const [users, setUsers] = useState([]);
  const [revenue, setRevenue] = useState([]);
  const [keys, setKeys] = useState(null);
  const [ml, setMl] = useState(null);
  const [retraining, setRetraining] = useState(false);
  const [apiSportsResult, setApiSportsResult] = useState(null);
  const [testingApi, setTestingApi] = useState(false);

  const load = () => {
    api.get("/admin/dashboard").then((r) => setDash(r.data));
    api.get("/admin/users").then((r) => setUsers(r.data));
    api.get("/admin/revenue").then((r) => setRevenue(r.data));
    api.get("/admin/api-keys").then((r) => setKeys(r.data));
    api.get("/admin/ml/meta").then((r) => setMl(r.data));
  };

  useEffect(() => { load(); }, []);

  const setRole = async (id, role) => {
    await api.patch(`/admin/users/${id}/role`, { role });
    load();
  };
  const removeUser = async (id) => {
    if (!confirm("Delete this user?")) return;
    await api.delete(`/admin/users/${id}`);
    load();
  };
  const retrainModels = async () => {
    if (!confirm("Retrain XGBoost + LightGBM ensemble on current data? Takes ~30s and recomputes every prediction.")) return;
    setRetraining(true);
    try {
      const { data } = await api.post("/admin/ml/retrain");
      setMl({ trained: true, meta: data.meta });
      alert(`Retrained.\nXGBoost test acc: ${(data.meta.xgb_test_accuracy * 100).toFixed(1)}%\nLightGBM test acc: ${(data.meta.lgb_test_accuracy * 100).toFixed(1)}%\nSamples: ${data.meta.total_samples}`);
    } catch (e) {
      alert("Retrain failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setRetraining(false);
    }
  };
  const testApiSports = async () => {
    setTestingApi(true);
    setApiSportsResult(null);
    try {
      const { data } = await api.get("/admin/api-sports/test");
      setApiSportsResult({ ok: true, ...data });
    } catch (e) {
      setApiSportsResult({ ok: false, detail: e.response?.data?.detail || e.message });
    } finally {
      setTestingApi(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-5 py-8" data-testid="admin-page">
        <div className="mb-8">
          <div className="text-[10px] uppercase tracking-[0.25em] text-amber-300 mb-1.5 font-bold">Admin console</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black uppercase tracking-tighter">Operations</h1>
        </div>

        {dash && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-10">
            <Stat label="Users" value={dash.total_users} icon={Users} />
            <Stat label="Premium" value={dash.premium_users} icon={Crown} />
            <Stat label="Games" value={dash.total_games} icon={Activity} />
            <Stat label="Predictions" value={dash.total_predictions} />
            <Stat label="Accuracy" value={`${dash.accuracy}%`} />
            <Stat label="Revenue" value={`$${dash.revenue_total}`} icon={DollarSign} accent="win" />
          </div>
        )}

        {/* ML status */}
        <section className="mb-10">
          <h2 className="font-display text-2xl uppercase tracking-tight mb-3 flex items-center gap-2"><Brain size={14} className="text-[#ff3b30]" /> ML Engine</h2>
          <div className="rounded-lg border border-white/10 bg-[#121214] p-5 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">Engine</div>
              <div className="font-display text-lg text-white mt-1">XGBoost + LightGBM</div>
              <div className={`text-[10px] uppercase tracking-[0.18em] font-bold mt-1 ${ml?.trained ? "text-emerald-300" : "text-amber-300"}`}>
                {ml?.trained ? "Trained" : "Untrained — fallback to statistical"}
              </div>
            </div>
            <Mini label="XGBoost test acc" value={ml?.meta?.xgb_test_accuracy ? `${(ml.meta.xgb_test_accuracy * 100).toFixed(1)}%` : "—"} />
            <Mini label="LightGBM test acc" value={ml?.meta?.lgb_test_accuracy ? `${(ml.meta.lgb_test_accuracy * 100).toFixed(1)}%` : "—"} />
            <Mini label="Training samples" value={ml?.meta?.total_samples ?? "—"} hint={ml?.meta ? `${ml.meta.real_samples} real + ${ml.meta.augmented_samples} synthetic` : null} />
          </div>
          <div className="mt-3 flex items-center gap-3">
            <button
              data-testid="ml-retrain-btn"
              onClick={retrainModels}
              disabled={retraining}
              className="inline-flex items-center gap-1.5 bg-[#ff3b30] hover:bg-[#dc2626] disabled:opacity-60 text-white px-4 py-2 rounded text-xs font-bold uppercase tracking-widest"
            >
              <RefreshCw size={12} className={retraining ? "animate-spin" : ""} />
              {retraining ? "Retraining..." : "Retrain models"}
            </button>
            {ml?.meta?.trained_at && (
              <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">
                Last trained: {new Date(ml.meta.trained_at).toLocaleString()}
              </span>
            )}
          </div>
        </section>

        {/* API Keys */}
        {keys && (
          <section className="mb-10">
            <h2 className="font-display text-2xl uppercase tracking-tight mb-3 flex items-center gap-2"><KeyRound size={14} className="text-[#ff3b30]" /> API Keys</h2>
            <div className="grid sm:grid-cols-2 gap-3">
              <KeyRow name="api-sports.io" host={keys.api_sports?.host} configured={keys.api_sports?.configured} />
              <KeyRow name="Stripe" configured={keys.stripe?.configured} />
            </div>
            <div className="mt-3 flex items-center gap-3">
              <button
                data-testid="api-sports-test-btn"
                onClick={testApiSports}
                disabled={testingApi}
                className="inline-flex items-center gap-1.5 border border-white/15 hover:border-white/30 text-white px-4 py-2 rounded text-xs font-bold uppercase tracking-widest"
              >
                <Zap size={12} /> {testingApi ? "Testing..." : "Test API-SPORTS"}
              </button>
              {apiSportsResult && (
                <span className={`text-[10px] uppercase tracking-[0.18em] font-bold ${apiSportsResult.ok ? "text-emerald-300" : "text-red-400"}`}>
                  {apiSportsResult.ok ? "Connected ✓" : `Failed: ${apiSportsResult.detail}`}
                </span>
              )}
            </div>
            {apiSportsResult?.ok && apiSportsResult.response && (
              <pre className="mt-3 text-[10px] text-zinc-400 bg-black/40 border border-white/5 rounded p-3 overflow-x-auto max-h-40">
{JSON.stringify(apiSportsResult.response, null, 2)}
              </pre>
            )}
            {!keys.api_sports?.configured && (
              <div className="mt-3 text-xs text-zinc-400 border border-amber-400/30 bg-amber-500/5 rounded p-3">
                <strong className="text-amber-300">Demo mode active.</strong> Add an API-SPORTS key to <code className="font-mono">backend/.env</code> as <code className="font-mono">API_SPORTS_KEY=your_key</code> and run <code className="font-mono">sudo supervisorctl restart backend</code> to switch to live data.
              </div>
            )}
          </section>
        )}

        {/* Users */}
        <section className="mb-10">
          <h2 className="font-display text-2xl uppercase tracking-tight mb-3">Users</h2>
          <div className="rounded-lg border border-white/10 bg-[#121214] overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 bg-black/30">
                <tr>
                  <th className="text-left px-4 py-2.5">Email</th>
                  <th className="text-left px-4 py-2.5">Name</th>
                  <th className="text-left px-4 py-2.5">Role</th>
                  <th className="text-left px-4 py-2.5">Premium Until</th>
                  <th className="text-right px-4 py-2.5">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-white/5">
                    <td className="px-4 py-2.5 text-white">{u.email}</td>
                    <td className="px-4 py-2.5 text-zinc-300">{u.name}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] uppercase tracking-[0.18em] font-bold ${roleClass(u.role)}`}>{u.role}</span>
                    </td>
                    <td className="px-4 py-2.5 text-zinc-400 tabular">{u.premium_until ? new Date(u.premium_until).toLocaleDateString() : "—"}</td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex justify-end gap-2">
                        <button data-testid={`grant-premium-${u.id}`} title="Grant premium" onClick={() => setRole(u.id, "premium")} className="p-1.5 rounded hover:bg-white/5 text-amber-300"><Crown size={14} /></button>
                        <button data-testid={`suspend-${u.id}`} title="Suspend" onClick={() => setRole(u.id, "suspended")} className="p-1.5 rounded hover:bg-white/5 text-zinc-400"><ShieldOff size={14} /></button>
                        <button data-testid={`delete-user-${u.id}`} title="Delete" onClick={() => removeUser(u.id)} className="p-1.5 rounded hover:bg-white/5 text-red-400"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Revenue */}
        <section>
          <h2 className="font-display text-2xl uppercase tracking-tight mb-3">Revenue & transactions</h2>
          <div className="rounded-lg border border-white/10 bg-[#121214] overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 bg-black/30">
                <tr>
                  <th className="text-left px-4 py-2.5">When</th>
                  <th className="text-left px-4 py-2.5">User</th>
                  <th className="text-left px-4 py-2.5">Package</th>
                  <th className="text-right px-4 py-2.5">Amount</th>
                  <th className="text-left px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {revenue.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-6 text-center text-zinc-500 text-xs">No transactions yet.</td></tr>
                )}
                {revenue.map((t) => (
                  <tr key={t.session_id} className="border-t border-white/5">
                    <td className="px-4 py-2.5 text-zinc-400 tabular">{new Date(t.created_at).toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-white">{t.user_email}</td>
                    <td className="px-4 py-2.5 text-zinc-300">{t.package_id}</td>
                    <td className="px-4 py-2.5 text-right text-white tabular">${t.amount}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] uppercase tracking-[0.18em] font-bold ${t.payment_status === "paid" ? "text-emerald-300" : "text-zinc-400"}`}>{t.payment_status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </Layout>
  );
}

function Stat({ label, value, icon: Icon, accent }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#121214] p-4">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</div>
        {Icon && <Icon size={14} className="text-zinc-500" />}
      </div>
      <div className={`font-num text-3xl tabular mt-2 ${accent === "win" ? "text-emerald-400" : "text-white"}`}>{value}</div>
    </div>
  );
}

function roleClass(role) {
  switch (role) {
    case "admin": return "text-amber-300";
    case "premium": return "text-emerald-300";
    case "suspended": return "text-red-400";
    default: return "text-zinc-300";
  }
}

function KeyRow({ name, host, configured }) {
  return (
    <div className="rounded border border-white/10 bg-[#121214] p-4 flex items-center justify-between">
      <div>
        <div className="text-white font-bold text-sm">{name}</div>
        {host && <div className="text-xs text-zinc-400 font-mono">{host}</div>}
      </div>
      <span className={`text-[10px] uppercase tracking-[0.18em] font-bold ${configured ? "text-emerald-300" : "text-amber-300"}`}>
        {configured ? "Connected" : "Demo Mode"}
      </span>
    </div>
  );
}

function Mini({ label, value, hint }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</div>
      <div className="font-num text-3xl tabular text-white mt-1">{value}</div>
      {hint && <div className="text-[10px] text-zinc-500 mt-0.5">{hint}</div>}
    </div>
  );
}
