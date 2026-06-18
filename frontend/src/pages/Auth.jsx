import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { useAuth } from "@/contexts/AuthContext";
import { formatApiError } from "@/lib/api";

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      nav(loc.state?.from || "/dashboard");
    } catch (e2) {
      setError(formatApiError(e2.response?.data?.detail) || e2.message);
    } finally {
      setLoading(false);
    }
  };
  return (
    <Layout>
      <div className="max-w-md mx-auto px-5 py-20">
        <h1 className="font-display text-4xl font-black uppercase tracking-tighter mb-2">Log in</h1>
        <p className="text-sm text-zinc-400 mb-6">Welcome back. Your edge awaits.</p>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Email" type="email" value={email} onChange={setEmail} testId="login-email" />
          <Field label="Password" type="password" value={password} onChange={setPassword} testId="login-password" />
          {error && <div data-testid="login-error" className="text-sm text-red-400 border border-red-500/30 bg-red-500/5 rounded px-3 py-2">{error}</div>}
          <button
            data-testid="login-submit"
            type="submit"
            disabled={loading}
            className="w-full bg-[#ff3b30] hover:bg-[#dc2626] disabled:opacity-60 text-white font-bold uppercase tracking-widest py-3 rounded transition-colors"
          >
            {loading ? "Signing in..." : "Log in"}
          </button>
        </form>
        <p className="mt-6 text-sm text-zinc-400">
          New here?{" "}
          <Link to="/register" data-testid="login-go-register" className="text-white underline">Create an account</Link>
        </p>
        <div className="mt-6 border-t border-white/10 pt-4 text-xs text-zinc-500">
      </div>
    </Layout>
  );
}

export function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, name);
      nav("/dashboard");
    } catch (e2) {
      setError(formatApiError(e2.response?.data?.detail) || e2.message);
    } finally {
      setLoading(false);
    }
  };
  return (
    <Layout>
      <div className="max-w-md mx-auto px-5 py-20">
        <h1 className="font-display text-4xl font-black uppercase tracking-tighter mb-2">Create account</h1>
        <p className="text-sm text-zinc-400 mb-6">90 seconds. No credit card.</p>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Name" type="text" value={name} onChange={setName} testId="register-name" />
          <Field label="Email" type="email" value={email} onChange={setEmail} testId="register-email" />
          <Field label="Password" type="password" value={password} onChange={setPassword} testId="register-password" />
          {error && <div data-testid="register-error" className="text-sm text-red-400 border border-red-500/30 bg-red-500/5 rounded px-3 py-2">{error}</div>}
          <button
            data-testid="register-submit"
            type="submit"
            disabled={loading}
            className="w-full bg-[#ff3b30] hover:bg-[#dc2626] disabled:opacity-60 text-white font-bold uppercase tracking-widest py-3 rounded"
          >
            {loading ? "Creating..." : "Sign up"}
          </button>
        </form>
        <p className="mt-6 text-sm text-zinc-400">
          Have an account?{" "}
          <Link to="/login" className="text-white underline">Log in</Link>
        </p>
        <div className="mb-1">Demo accounts:</div>
          <div><code className="font-mono">admin@courtvisionai.com / ChangeOnFirstLogin123</code></div>
          <div><code className="font-mono">pro@courtvisionai.com / Pro123!</code></div>
          <div><code className="font-mono">user@courtvisionai.com / User123!</code></div>
        </div>
      </div>
      
    </Layout>
  );
}

function Field({ label, type, value, onChange, testId }) {
  return (
    <label className="block">
      <span className="text-[10px] tracking-[0.18em] uppercase text-zinc-400 font-bold">{label}</span>
      <input
        data-testid={testId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="mt-1.5 w-full bg-[#121214] border border-white/10 focus:border-[#ff3b30] focus:ring-0 outline-none rounded px-3 py-2.5 text-white text-sm"
      />
    </label>
  );
}
