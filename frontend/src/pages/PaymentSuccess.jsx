import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import { useSearchParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Check, Loader2 } from "lucide-react";

const MAX_ATTEMPTS = 6;

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [status, setStatus] = useState("checking");
  const [info, setInfo] = useState(null);
  const { refreshMe } = useAuth();

  useEffect(() => {
    if (!sessionId) {
      setStatus("error");
      return;
    }
    let cancelled = false;

    const poll = async (attempt = 0) => {
      if (cancelled) return;
      try {
        const { data } = await api.get(`/checkout/status/${sessionId}`);
        if (data.payment_status === "paid") {
          setInfo(data);
          setStatus("paid");
          await refreshMe();
          return;
        }
        if (data.status === "expired") {
          setStatus("expired");
          return;
        }
        if (attempt >= MAX_ATTEMPTS) {
          setStatus("timeout");
          return;
        }
        setTimeout(() => poll(attempt + 1), 2000);
      } catch (e) {
        setStatus("error");
      }
    };
    poll();

    return () => { cancelled = true; };
  }, [sessionId, refreshMe]);

  return (
    <Layout>
      <div className="max-w-md mx-auto px-5 py-24 text-center" data-testid="payment-success">
        {status === "checking" && (
          <>
            <Loader2 className="mx-auto animate-spin text-[#ff3b30]" />
            <h1 className="font-display text-3xl font-black uppercase tracking-tighter mt-6">Confirming payment</h1>
            <p className="text-sm text-zinc-400 mt-2">Hang tight &mdash; this only takes a few seconds.</p>
          </>
        )}
        {status === "paid" && (
          <>
            <Check className="mx-auto text-emerald-400" size={42} />
            <h1 className="font-display text-3xl font-black uppercase tracking-tighter mt-6">You're in.</h1>
            <p className="text-sm text-zinc-400 mt-2">Premium access is now active on your account.</p>
            <Link to="/dashboard" className="inline-block mt-6 bg-[#ff3b30] hover:bg-[#dc2626] text-white px-6 py-3 rounded font-bold uppercase tracking-widest text-sm">
              Go to dashboard
            </Link>
          </>
        )}
        {(status === "error" || status === "expired" || status === "timeout") && (
          <>
            <h1 className="font-display text-3xl font-black uppercase tracking-tighter">Payment {status === "expired" ? "expired" : "unconfirmed"}</h1>
            <p className="text-sm text-zinc-400 mt-2">
              We couldn&apos;t confirm your payment. If you completed the checkout, refresh in a few seconds, or contact support.
            </p>
            <Link to="/pricing" className="inline-block mt-6 border border-white/15 text-white px-6 py-3 rounded font-bold uppercase tracking-widest text-sm">
              Back to pricing
            </Link>
          </>
        )}
      </div>
    </Layout>
  );
}
