import { useState } from "react";

const BASE_DOMAIN = import.meta.env.VITE_BASE_DOMAIN || "syyaimeiq.com";
const API_BASE =
  import.meta.env.VITE_PUBLIC_API || `https://api.${BASE_DOMAIN}`;

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 32);
}

export default function SignupPage() {
  const [form, setForm] = useState({
    company_name: "",
    slug: "",
    admin_email: "",
    admin_name: "",
    password: "",
    phone: "",
  });
  const [slugManual, setSlugManual] = useState(false);
  const [slugStatus, setSlugStatus] = useState(null); // null | "checking" | "available" | "taken"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  const update = (field) => (e) => {
    const val = e.target.value;
    setForm((f) => {
      const next = { ...f, [field]: val };
      if (field === "company_name" && !slugManual) {
        next.slug = slugify(val);
      }
      return next;
    });
    if (field === "slug") {
      setSlugManual(true);
      checkSlug(val);
    }
    if (field === "company_name" && !slugManual) {
      checkSlug(slugify(val));
    }
  };

  let slugTimer;
  const checkSlug = (slug) => {
    if (!slug || slug.length < 3) {
      setSlugStatus(null);
      return;
    }
    clearTimeout(slugTimer);
    setSlugStatus("checking");
    slugTimer = setTimeout(async () => {
      try {
        const r = await fetch(
          `${API_BASE}/api/v1/public/check-slug?slug=${slug}`,
        );
        const d = await r.json();
        setSlugStatus(d.available ? "available" : "taken");
      } catch {
        setSlugStatus(null);
      }
    }, 500);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/public/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Signup failed");
      setSuccess(d);
      // Redirect to tenant subdomain after short delay
      setTimeout(() => {
        window.location.href = `https://${form.slug}.${BASE_DOMAIN}/login`;
      }, 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-lg w-full text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            You're all set!
          </h2>
          <p className="text-gray-500 mb-6">
            Your ERP is being provisioned. It'll be ready in about 30 seconds.
          </p>
          <div className="bg-blue-50 rounded-xl p-5 mb-6 text-left">
            <p className="text-sm text-gray-500 mb-1">Your ERP URL</p>
            <a
              href={success.erp_url}
              className="text-blue-700 font-bold text-lg hover:underline"
            >
              {success.erp_url}
            </a>
          </div>
          {success.checkout_url ? (
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Your 14-day free trial is active. Subscribe now to lock in your
                price.
              </p>
              <a
                href={success.checkout_url}
                className="block bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold hover:bg-blue-800 mb-3"
              >
                Subscribe — ₹12,999/month →
              </a>
            </div>
          ) : null}
          <a
            href={success.erp_url}
            className="block border-2 border-blue-700 text-blue-700 py-3 px-6 rounded-xl font-semibold hover:bg-blue-50"
          >
            Open My ERP →
          </a>
          <p className="text-xs text-gray-400 mt-4">
            Check your email for login details.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left — value prop */}
        <div className="text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-yellow-400 rounded-xl flex items-center justify-center text-blue-900 font-black text-xl">
              M
            </div>
            <span className="text-2xl font-bold">Syyaim EIQ ERP</span>
          </div>
          <h1 className="text-4xl font-black mb-4 leading-tight">
            AI-powered ERP
            <br />
            for Indian manufacturers
          </h1>
          <p className="text-blue-200 text-lg mb-8">
            Live in 60 seconds. No IT team needed.
          </p>
          <div className="space-y-4">
            {[
              ["🤖", "AI Lead Scoring", "Every lead scored automatically"],
              ["✅", "Smart PR Approval", "Policy checks before you approve"],
              ["📦", "MRP Planning", "Auto-raise POs when stock is low"],
              ["💰", "Payroll Audit", "Anomaly detection before disbursement"],
              ["📊", "Financial Insights", "Weekly AI commentary on your P&L"],
            ].map(([icon, title, desc]) => (
              <div key={title} className="flex items-start gap-3">
                <span className="text-2xl">{icon}</span>
                <div>
                  <p className="font-semibold">{title}</p>
                  <p className="text-blue-300 text-sm">{desc}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-8 bg-white/10 rounded-xl p-4">
            <p className="font-bold text-lg">₹12,999 / month</p>
            <p className="text-blue-300 text-sm">
              All modules · 25 users · 2,500 AI actions
            </p>
            <p className="text-yellow-300 text-sm font-semibold mt-1">
              14 days free trial — no credit card
            </p>
          </div>
        </div>

        {/* Right — signup form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-1">
            Start your free trial
          </h2>
          <p className="text-gray-400 text-sm mb-6">
            14 days free. Cancel anytime.
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Name
              </label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.company_name}
                onChange={update("company_name")}
                placeholder="Acme Manufacturing Pvt Ltd"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your ERP Subdomain
              </label>
              <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
                <input
                  className="flex-1 px-3 py-2 outline-none"
                  value={form.slug}
                  onChange={update("slug")}
                  placeholder="acme"
                  required
                />
                <span className="bg-gray-50 px-3 py-2 text-gray-500 text-sm border-l border-gray-300">
                  .{BASE_DOMAIN}
                </span>
              </div>
              {form.slug.length >= 3 && (
                <p
                  className={`text-xs mt-1 ${
                    slugStatus === "available"
                      ? "text-green-600"
                      : slugStatus === "taken"
                        ? "text-red-500"
                        : "text-gray-400"
                  }`}
                >
                  {slugStatus === "checking" && "Checking…"}
                  {slugStatus === "available" &&
                    `✓ ${form.slug}.${BASE_DOMAIN} is available`}
                  {slugStatus === "taken" &&
                    `✗ Already taken — try another name`}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Name
              </label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.admin_name}
                onChange={update("admin_name")}
                placeholder="Rajesh Kumar"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Work Email
              </label>
              <input
                type="email"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.admin_email}
                onChange={update("admin_email")}
                placeholder="rajesh@acme.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.password}
                onChange={update("password")}
                placeholder="Min. 8 characters"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone (optional)
              </label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.phone}
                onChange={update("phone")}
                placeholder="+91 98765 43210"
              />
            </div>

            <button
              type="submit"
              disabled={loading || slugStatus === "taken"}
              className="w-full bg-blue-700 text-white py-3 rounded-xl font-semibold text-lg hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Creating your ERP…" : "Start Free Trial →"}
            </button>

            <p className="text-center text-xs text-gray-400">
              By signing up you agree to our Terms of Service and Privacy
              Policy. No credit card required for trial.
            </p>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-500">
              Already have an account?{" "}
              <a
                href="/login"
                className="text-blue-700 font-medium hover:underline"
              >
                Sign in
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
