"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-client";
import s from "./auth.module.css";

type Tab = "signin" | "signup";

const SIGNALS = [
  {
    dot: s.sigDotRed,
    kicker: "CRITICAL",
    title: "Login loop after v4.7.8",
    meta: "47 reports · Play 31 · App 12 · X 4",
    time: "48h spike",
  },
  {
    dot: s.sigDotAmber,
    kicker: "FEATURE REQUEST",
    title: "Dark mode asks growing",
    meta: "89 mentions · all 4 channels",
    time: "+34% WoW",
  },
  {
    dot: s.sigDotGreen,
    kicker: "POSITIVE",
    title: "Onboarding v2 landing well",
    meta: "5★ mentions up since v2.4",
    time: "12 unprompted",
  },
];

export default function AuthPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const nextParam =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("next") ?? "/onboarding"
      : "/onboarding";

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const W = 600, H = 800, step = 22;
    let markup = "";
    for (let y = step; y < H; y += step) {
      for (let x = step; x < W; x += step) {
        const n = ((x * 73 + y * 131) % 100);
        if (n < 4) {
          markup += `<circle cx="${x}" cy="${y}" r="2.2" fill="#00a889" opacity="0.55"/>`;
        } else if (n < 70) {
          markup += `<circle cx="${x}" cy="${y}" r="1" fill="#a3a4a6" opacity="0.35"/>`;
        }
      }
    }
    svg.innerHTML = markup;
  }, []);

  async function handleGoogleSignIn() {
    setError(null);
    setLoading(true);
    try {
      const supabase = createClient();
      const origin = window.location.origin;
      const { error: err } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${origin}/auth/callback?next=${encodeURIComponent(nextParam)}`,
          queryParams: { access_type: "offline", prompt: "consent" },
        },
      });
      if (err) throw err;
    } catch (caught) {
      setLoading(false);
      setError(caught instanceof Error ? caught.message : "Google sign-in could not start.");
    }
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();

    try {
      if (tab === "signup") {
        const { error: err } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { name: name || email.split("@")[0] } },
        });
        if (err) throw err;
        router.push("/onboarding");
      } else {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
        router.push(nextParam);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function switchTab(t: Tab) {
    setTab(t);
    setError(null);
  }

  return (
    <div className={s.split}>
      {/* LEFT — form */}
      <section className={s.left}>
        <div className={s.logoRow}>
          <a href="/marketing" className={s.logo}>
            <span className={s.logoDot} />
            Rivue
          </a>
          <a href="/marketing" className={s.backLink}>← Back to site</a>
        </div>

        <div className={s.formWrap}>
          <div className={s.sectionLabel}>
            <span className="dash" style={{ width: 22, height: 1, background: "#6b6c6f", display: "inline-block", flexShrink: 0 }} />
            <span>§ SIGN IN</span>
          </div>

          <h1 className={s.headline}>
            {tab === "signin" ? "Welcome back." : "Get started."}
          </h1>
          <p className={s.lede}>
            {tab === "signin"
              ? "Your morning digest is waiting."
              : "Connect your first feedback channel in minutes."}
          </p>

          {/* Tabs */}
          <div className={s.tabs}>
            <button
              className={`${s.tab} ${tab === "signin" ? s.tabActive : ""}`}
              onClick={() => switchTab("signin")}
              type="button"
            >
              Sign in
            </button>
            <button
              className={`${s.tab} ${tab === "signup" ? s.tabActive : ""}`}
              onClick={() => switchTab("signup")}
              type="button"
            >
              Create account
            </button>
          </div>

          {/* Google OAuth */}
          <button className={s.oauth} onClick={handleGoogleSignIn} disabled={loading} type="button">
            <GoogleIcon />
            {loading ? "Opening Google…" : "Continue with Google"}
          </button>

          <div className={s.divider}>
            <div className={s.dividerLine} />
            <span className={s.dividerText}>OR</span>
            <div className={s.dividerLine} />
          </div>

          {/* Email form */}
          <form onSubmit={handleEmailSubmit}>
            {tab === "signup" && (
              <div className={s.fieldGroup}>
                <label className={s.label}>Your name</label>
                <input
                  className={s.input}
                  type="text"
                  placeholder="Ishita Rao"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                />
              </div>
            )}

            <div className={s.fieldGroup}>
              <label className={s.label}>Work email</label>
              <input
                className={s.input}
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className={s.fieldGroup}>
              <div className={s.fieldRow}>
                <label className={s.label} style={{ marginBottom: 0 }}>Password</label>
                {tab === "signin" && (
                  <a href="#" className={s.forgotLink}>Forgot?</a>
                )}
              </div>
              <input
                className={s.input}
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={tab === "signup" ? "new-password" : "current-password"}
              />
            </div>

            {error && <p className={s.errorMsg}>{error}</p>}

            <button className={s.btnPrimary} type="submit" disabled={loading}>
              {loading
                ? "Just a moment…"
                : tab === "signin"
                ? "Sign in →"
                : "Create account →"}
            </button>
          </form>

          <p className={s.switchPrompt}>
            {tab === "signin" ? (
              <>No account yet?{" "}
                <button className={s.switchLink} onClick={() => switchTab("signup")} type="button">
                  Start free
                </button>
              </>
            ) : (
              <>Already have an account?{" "}
                <button className={s.switchLink} onClick={() => switchTab("signin")} type="button">
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>

        <div className={s.footMeta}>
          <span>SOC 2 TYPE II · EU HOSTED</span>
          <span>V 1.4 · RIVUE LABS</span>
        </div>
      </section>

      {/* RIGHT — live pulse teaser */}
      <aside className={s.right}>
        <div className={s.pulseWrap}>
          <div className={s.liveLabel}>
            <span className={s.liveDot} />
            LIVE · RIGHT NOW
          </div>

          <h2 className={s.pulseH2}>
            While you were out,<br />
            Rivue found <em>three things.</em>
          </h2>
          <p className={s.pulseLede}>
            Every channel your users talk on — watched continuously, correlated
            automatically, ranked by urgency. That&apos;s what&apos;s on the other
            side of this button.
          </p>
        </div>

        <div className={s.pulseCard}>
          <div className={s.cardHeader}>
            <span className={s.cardHeaderLeft}>TODAY&apos;S TOP 3 · 06:00</span>
            <span className={s.cardHeaderRight}>● LIVE</span>
          </div>

          {SIGNALS.map((sig) => (
            <div key={sig.kicker} className={s.sigRow}>
              <span className={`${s.sigDot} ${sig.dot}`} />
              <div>
                <div className={s.sigKicker}>{sig.kicker}</div>
                <div className={s.sigTitle}>{sig.title}</div>
                <div className={s.sigMeta}>{sig.meta}</div>
              </div>
              <span className={s.sigTime}>{sig.time}</span>
            </div>
          ))}
        </div>

        <div className={s.trustedLabel}>
          · TRUSTED BY PRODUCT TEAMS AT KINDLING, MERIDIAN, VELLUM, QUARTZ ·
        </div>

        {/* Ambient dot field */}
        <svg
          ref={svgRef}
          className={s.dotField}
          viewBox="0 0 600 800"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        />
      </aside>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" aria-hidden="true">
      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A9 9 0 009 18z" />
      <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A9 9 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" />
      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A9 9 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" />
    </svg>
  );
}
