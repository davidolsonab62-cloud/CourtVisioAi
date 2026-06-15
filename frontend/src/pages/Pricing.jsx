import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Check, Crown } from "lucide-react";

export default function Pricing() {
  const [packages, setPackages] = useState([]);
  const [loadingPkg, setLoadingPkg] = useState(null);
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    api.get("/packages").then((r) => setPackages(r.data));
  }, []);

  const startCheckout = async (pkg_id) => {
    if (!user) {
      nav("/login", { state: { from: "/pricing" } });
      return;
    }
    setLoadingPkg(pkg_id);
    try {
      const { data } = await api.post("/checkout/session", {
        package_id: pkg_id,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      alert("Could not start checkout: " + (e.response?.data?.detail || e.message || String(e)));
    } finally {
      setLoadingPkg(null);
    }
  };

  const features = [
    "Unlimited daily predictions",
    "85-99 confidence picks",
    "Full model breakdown",
    "League-by-league ROI",
    "Best Value Bet alerts",
    "Ad-free experience",
  ];

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-5 py-12" data-testid="pricing-page">
        <div className="text-center mb-12">
          <div className="text-[10px] uppercase tracking-[0.25em] text-[#ff3b30] mb-2 font-bold">Premium membership</div>
          <h1 className="font-display text-5xl sm:text-6xl font-black uppercase tracking-tighter">Pick the season.</h1>
          <p className="text-zinc-400 mt-4 max-w-xl mx-auto">Cancel anytime. All plans include the full feature set — just choose your horizon.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {packages.map((pkg, idx) => {
            const popular = pkg.id === "monthly";
            return (
              <div
                key={pkg.id}
                data-testid={`pricing-card-${pkg.id}`}
                className={`relative rounded-lg border p-5 flex flex-col ${popular ? "border-[#ff3b30]/50 bg-[#1a0e0c]" : "border-white/10 bg-[#121214]"}`}
              >
                {popular && (
                  <span className="absolute -top-2 left-5 px-2 py-0.5 text-[9px] uppercase tracking-[0.18em] font-bold bg-[#ff3b30] text-white rounded">Most popular</span>
                )}
                <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{pkg.label}</div>
                <div className="mt-2 mb-1">
                  <span className="font-num text-5xl text-white tabular">${pkg.amount}</span>
                </div>
                <div className="text-xs text-zinc-500 mb-6">${(pkg.amount / pkg.days).toFixed(2)} / day</div>
                <ul className="space-y-2 text-sm text-zinc-300 mb-6 flex-1">
                  {features.map((f) => (
                    <li key={f} className="flex items-start gap-2"><Check size={14} className="text-emerald-400 mt-1 shrink-0" /> {f}</li>
                  ))}
                </ul>
                <button
                  data-testid={`subscribe-${pkg.id}`}
                  disabled={loadingPkg === pkg.id}
                  onClick={() => startCheckout(pkg.id)}
                  className={`w-full py-3 rounded font-bold uppercase tracking-widest text-sm transition-colors ${popular ? "bg-[#ff3b30] hover:bg-[#dc2626] text-white" : "bg-white text-black hover:bg-zinc-200"} disabled:opacity-60`}
                >
                  {loadingPkg === pkg.id ? "Redirecting…" : user?.is_premium ? "Extend" : "Subscribe"}
                </button>
              </div>
            );
          })}
        </div>

        <div className="rounded-lg border border-white/10 bg-[#121214] p-5 text-xs text-zinc-500 text-center">
          Payments are processed by Stripe. CourtVision AI accepts cards globally; in supported regions cryptocurrency
          and PayPal can be added on request.
        </div>

        <p className="mt-12 text-[11px] text-center text-zinc-500">
          Predictions are <span className="text-amber-300">statistical estimates</span> and not guaranteed outcomes.
        </p>
      </div>
    </Layout>
  );
}
