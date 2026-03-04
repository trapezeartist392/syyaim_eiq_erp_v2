import { useState, useEffect } from "react";
import api from "../utils/api";

/**
 * TrialBanner — shown at the top of the ERP layout.
 * Disappears once subscribed.
 */
export default function TrialBanner() {
  const [billing, setBilling] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/billing/status")
      .then((r) => setBilling(r.data))
      .catch(() => {});
  }, []);

  if (!billing) return null;
  if (billing.status === "active" && !billing.trial_days_left) return null;

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const r = await api.post("/billing/create-checkout");
      window.location.href = r.data.checkout_url;
    } catch (e) {
      alert("Could not start checkout. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handlePortal = async () => {
    setLoading(true);
    try {
      const r = await api.post("/billing/portal");
      window.location.href = r.data.portal_url;
    } catch (e) {
      alert("Could not open billing portal.");
    } finally {
      setLoading(false);
    }
  };

  // Suspended
  if (billing.status === "suspended") {
    return (
      <div className="bg-red-600 text-white px-4 py-2 flex items-center justify-between text-sm">
        <span>⚠️ Your account is suspended due to a payment issue.</span>
        <button
          onClick={handlePortal}
          className="bg-white text-red-600 px-3 py-1 rounded font-semibold hover:bg-red-50"
        >
          Update Payment →
        </button>
      </div>
    );
  }

  // Trial warning (≤5 days left)
  const daysLeft = billing.trial_days_left;
  if (billing.status === "trial" && daysLeft !== null) {
    const urgent = daysLeft <= 3;
    return (
      <div className={`${urgent ? "bg-red-500" : "bg-amber-500"} text-white px-4 py-2 flex items-center justify-between text-sm`}>
        <div className="flex items-center gap-3">
          <span>{urgent ? "🚨" : "⏳"}</span>
          <span>
            {daysLeft === 0
              ? "Your trial expires today!"
              : `Trial ends in ${daysLeft} day${daysLeft !== 1 ? "s" : ""}.`}
            {" "}Subscribe now to keep your data.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-white/80">₹12,999/mo</span>
          <button
            onClick={handleSubscribe}
            disabled={loading}
            className="bg-white text-amber-700 px-3 py-1 rounded font-semibold hover:bg-amber-50 disabled:opacity-60"
          >
            {loading ? "…" : "Subscribe Now →"}
          </button>
        </div>
      </div>
    );
  }

  // AI actions warning (>80% used)
  const pctUsed = billing.ai_actions_limit > 0
    ? (billing.ai_actions_used / billing.ai_actions_limit) * 100
    : 0;

  if (pctUsed >= 80) {
    return (
      <div className="bg-blue-600 text-white px-4 py-2 flex items-center justify-between text-sm">
        <span>
          🤖 AI actions: {billing.ai_actions_used}/{billing.ai_actions_limit} used ({Math.round(pctUsed)}%).
          {pctUsed >= 100 ? " Limit reached — agents paused." : " Running low."}
        </span>
        <button
          onClick={handlePortal}
          className="bg-white text-blue-700 px-3 py-1 rounded font-semibold hover:bg-blue-50"
        >
          Manage Plan →
        </button>
      </div>
    );
  }

  return null;
}
