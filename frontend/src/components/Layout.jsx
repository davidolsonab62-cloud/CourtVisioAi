import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { LogOut, User, Crown, Menu, X } from "lucide-react";
import { useState } from "react";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/matches", label: "Match Center" },
  { to: "/performance", label: "Performance" },
  { to: "/pricing", label: "Pricing" },
];

export function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);

  return (
    <header className="glass sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-5 py-3 flex items-center justify-between">
        <Link to="/" data-testid="nav-logo" className="flex items-center gap-2">
          <span className="inline-block w-8 h-8 rounded bg-[#ff3b30] flex items-center justify-center font-display text-white text-lg leading-none">C</span>
          <span className="font-display font-extrabold tracking-tight text-white text-xl uppercase">CourtVision <span className="text-[#ff3b30]">AI</span></span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              data-testid={`nav-link-${n.label.toLowerCase().replace(/\s/g, "-")}`}
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm font-semibold tracking-tight transition-colors ${isActive ? "text-white bg-white/5" : "text-zinc-400 hover:text-white"}`
              }
            >
              {n.label}
            </NavLink>
          ))}
          {user && user.role === "admin" && (
            <NavLink
              to="/admin"
              data-testid="nav-link-admin"
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm font-semibold tracking-tight transition-colors ${isActive ? "text-white bg-white/5" : "text-amber-300 hover:text-amber-200"}`
              }
            >
              Admin
            </NavLink>
          )}
        </nav>

        <div className="hidden md:flex items-center gap-2">
          {user && user !== false ? (
            <>
              {user.is_premium && (
                <span className="hidden lg:flex items-center gap-1 text-[10px] uppercase tracking-[0.18em] text-amber-300 font-bold px-2 py-1 rounded border border-amber-400/30">
                  <Crown size={12} /> Premium
                </span>
              )}
              <Link
                data-testid="nav-profile-btn"
                to="/profile"
                className="px-3 py-2 rounded text-sm font-semibold text-zinc-300 hover:text-white inline-flex items-center gap-1.5"
              >
                <User size={14} /> {user.name?.split(" ")[0]}
              </Link>
              <button
                data-testid="nav-logout-btn"
                onClick={async () => { await logout(); nav("/"); }}
                className="px-3 py-2 rounded text-sm font-semibold text-zinc-400 hover:text-white inline-flex items-center gap-1.5"
              >
                <LogOut size={14} />
              </button>
            </>
          ) : (
            <>
              <Link
                data-testid="nav-login-btn"
                to="/login"
                className="px-3 py-2 rounded text-sm font-semibold text-zinc-300 hover:text-white"
              >
                Log in
              </Link>
              <Link
                data-testid="nav-signup-btn"
                to="/register"
                className="px-4 py-2 rounded text-sm font-bold uppercase tracking-widest bg-[#ff3b30] text-white hover:bg-[#dc2626] transition-colors"
              >
                Sign up
              </Link>
            </>
          )}
        </div>

        <button data-testid="mobile-menu-toggle" className="md:hidden text-white" onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-white/10 px-5 py-3 flex flex-col gap-2 bg-[#0a0a0b]">
          {navItems.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm font-semibold ${isActive ? "bg-white/5 text-white" : "text-zinc-400"}`
              }
            >
              {n.label}
            </NavLink>
          ))}
          {user && user.role === "admin" && (
            <NavLink to="/admin" onClick={() => setOpen(false)} className="px-3 py-2 rounded text-sm font-semibold text-amber-300">Admin</NavLink>
          )}
          {user && user !== false ? (
            <>
              <Link to="/profile" onClick={() => setOpen(false)} className="px-3 py-2 rounded text-sm text-zinc-300">Profile</Link>
              <button onClick={async () => { setOpen(false); await logout(); nav("/"); }} className="px-3 py-2 text-left rounded text-sm text-zinc-400">Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setOpen(false)} className="px-3 py-2 rounded text-sm text-zinc-300">Log in</Link>
              <Link to="/register" onClick={() => setOpen(false)} className="px-3 py-2 rounded text-sm font-bold bg-[#ff3b30] text-white">Sign up</Link>
            </>
          )}
        </div>
      )}
    </header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-white/10 mt-20">
      <div className="max-w-7xl mx-auto px-5 py-10 grid md:grid-cols-3 gap-6 text-sm text-zinc-400">
        <div>
          <div className="font-display text-white text-lg uppercase mb-2">CourtVision <span className="text-[#ff3b30]">AI</span></div>
          <p className="text-xs leading-relaxed text-zinc-500">
            Statistical edge across every basketball league on earth.
          </p>
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500 mb-2">Product</div>
          <ul className="space-y-1 text-zinc-300">
            <li><Link to="/dashboard">Dashboard</Link></li>
            <li><Link to="/matches">Match Center</Link></li>
            <li><Link to="/pricing">Pricing</Link></li>
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500 mb-2">Legal</div>
          <p className="text-[11px] leading-relaxed text-zinc-500">
            Predictions are <span className="text-amber-300">statistical estimates</span> and not guaranteed outcomes.
            Bet responsibly. Must be 18+ or of local legal age.
          </p>
        </div>
      </div>
      <div className="border-t border-white/10 text-center text-[11px] text-zinc-600 py-4">
        © {new Date().getFullYear()} CourtVision AI
      </div>
    </footer>
  );
}

export function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0b]">
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
