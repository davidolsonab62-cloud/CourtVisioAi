import { Link } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { ArrowRight, BarChart3, Brain, Globe, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";

const HERO_IMG = "https://images.pexels.com/photos/15828942/pexels-photo-15828942.jpeg";
const DUNK_IMG = "https://images.unsplash.com/photo-1608245449230-4ac19066d2d0?crop=entropy&cs=srgb&fm=jpg";

export default function Landing() {
  return (
    <Layout>
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url('${HERO_IMG}')`, filter: "brightness(0.35) saturate(1.1)" }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0b]/60 via-[#0a0a0b]/70 to-[#0a0a0b]" />
        <div className="grain absolute inset-0" />

        <div className="relative max-w-7xl mx-auto px-5 pt-24 pb-32">
          <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.25em] text-zinc-400 border border-white/10 px-3 py-1 rounded mb-6">
            <span className="live-dot" />
            XGBoost + LightGBM Ensemble. Real data. Zero hype.
          </div>
          <h1 className="font-display text-5xl sm:text-7xl lg:text-8xl font-black uppercase leading-[0.95] tracking-tighter text-white max-w-4xl">
            Predict the <span className="text-[#ff3b30]">play</span><br />before the tip.
          </h1>
          <p className="mt-6 max-w-xl text-zinc-300 text-base sm:text-lg leading-relaxed">
            Statistical ensemble predictions across NBA, EuroLeague, WNBA, NCAA and 12+ international leagues —
            grounded in pace, efficiency, rest, travel & market signals.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              data-testid="hero-cta-signup"
              to="/register"
              className="inline-flex items-center gap-2 bg-[#ff3b30] hover:bg-[#dc2626] text-white px-6 py-3.5 rounded font-bold uppercase tracking-widest text-sm transition-colors"
            >
              Get the edge <ArrowRight size={16} />
            </Link>
            <Link
              data-testid="hero-cta-dashboard"
              to="/dashboard"
              className="inline-flex items-center gap-2 border border-white/15 hover:border-white/30 text-white px-6 py-3.5 rounded font-bold uppercase tracking-widest text-sm transition-colors"
            >
              View live picks
            </Link>
          </div>

          <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl">
            {[
              { label: "Leagues Covered", value: "16+" },
              { label: "Model Accuracy", value: "70.2%" },
              { label: "ROI (21d)", value: "+34.1%" },
              { label: "Predictions / Day", value: "120+" },
            ].map((s) => (
              <div key={s.label} className="border-l border-white/10 pl-4">
                <div className="font-num text-4xl text-white tabular">{s.value}</div>
                <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW */}
      <section className="max-w-7xl mx-auto px-5 py-24">
        <div className="grid lg:grid-cols-[1.2fr_1fr] gap-12 items-end mb-12">
          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-[#ff3b30] mb-3 font-bold">The system</div>
            <h2 className="font-display text-4xl sm:text-5xl font-extrabold uppercase tracking-tighter">
              Four signals.<br />One verdict.
            </h2>
          </div>
          <p className="text-zinc-400 leading-relaxed">
            We blend Elo, offensive/defensive efficiency, recent form, and head-to-head into a calibrated
            win probability. Then we layer in rest days, travel distance & injuries.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: Brain, title: "XGBoost + LightGBM", body: "Two gradient-boosted ensembles blended with our statistical engine for calibrated win probabilities." },
            { icon: BarChart3, title: "Deterministic Outputs", body: "Same game, same prediction. Every time. No randomness." },
            { icon: Globe, title: "Global Coverage", body: "NBA, EuroLeague, ACB, LBA, BBL, PBA, B.League — and more." },
            { icon: ShieldCheck, title: "Risk-Aware", body: "Confidence tiers gate which picks ever reach your feed." },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title} className="card-hover rounded-lg border border-white/10 bg-[#121214] p-5">
              <Icon size={20} className="text-[#ff3b30] mb-4" />
              <div className="font-display text-lg font-bold mb-1.5">{title}</div>
              <p className="text-sm text-zinc-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* PREMIUM SECTION */}
      <section className="max-w-7xl mx-auto px-5 py-24 grid lg:grid-cols-2 gap-12 items-center">
        <div
          className="aspect-[4/5] rounded-lg bg-cover bg-center border border-white/10"
          style={{ backgroundImage: `url('${DUNK_IMG}')` }}
        />
        <div>
          <div className="text-[10px] uppercase tracking-[0.25em] text-[#ff3b30] mb-3 font-bold">Premium picks</div>
          <h2 className="font-display text-4xl sm:text-5xl font-extrabold uppercase tracking-tighter mb-4">
            The 90+ confidence club.
          </h2>
          <p className="text-zinc-400 leading-relaxed mb-6">
            Free users see anything up to 84 confidence — perfect for entertainment. Premium members unlock
            every 85+ pick, advanced model breakdowns, ROI tracking by league, and the elite 90-95 tier.
          </p>
          <ul className="space-y-3 text-sm">
            {["Unlimited daily predictions", "85-99 confidence picks", "Advanced model breakdowns", "League-by-league ROI charts", "Ad-free experience"].map((t) => (
              <li key={t} className="flex items-center gap-2 text-zinc-200">
                <Sparkles size={14} className="text-amber-400" /> {t}
              </li>
            ))}
          </ul>
          <Link
            data-testid="landing-premium-cta"
            to="/pricing"
            className="mt-8 inline-flex items-center gap-2 bg-[#ff3b30] hover:bg-[#dc2626] text-white px-6 py-3 rounded font-bold uppercase tracking-widest text-sm"
          >
            See pricing <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* DISCLAIMER */}
      <section className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-5 py-10 text-center">
          <p className="text-xs text-zinc-500 max-w-2xl mx-auto">
            CourtVision AI predictions are <span className="text-amber-300">statistical estimates</span> based on historical and current data.
            They are not guaranteed outcomes. Always bet responsibly. 18+ only.
          </p>
        </div>
      </section>
    </Layout>
  );
}
