"use client";
import { useEffect, useRef } from "react";
import s from "./marketing.module.css";

const TABS = [
  "Play Console",
  "App Store Conn…",
  "YouTube Studio",
  "X / mentions",
  "Zendesk",
];

const REVIEWS = [
  { stars: "★☆☆☆☆", text: "App crashes every time I open SIP..." },
  { stars: "★☆☆☆☆", text: "Same issue as last update, still broken" },
  { stars: "★★☆☆☆", text: "Good app but login never works" },
  { stars: "★☆☆☆☆", text: "How is this still broken??" },
  { stars: "★★☆☆☆", text: "Lost my data after updating" },
  { stars: "★☆☆☆☆", text: "Can't even sign in anymore" },
];

const SIGNALS = [
  {
    tone: "red" as const,
    label: "CRITICAL",
    title: "Login loop after v4.7.8",
    meta: "47 reports · Play 31 · App 12 · X 4",
    trend: "48h spike",
  },
  {
    tone: "amber" as const,
    label: "FEATURE REQUEST",
    title: "Dark mode asks growing",
    meta: "89 mentions · all 4 channels",
    trend: "+34% WoW",
  },
  {
    tone: "green" as const,
    label: "POSITIVE",
    title: "Onboarding v2 landing well",
    meta: "5★ mentions up 34%",
    trend: "12 unprompted",
  },
];

const CHANNELS = [
  { name: "Play Store", count: "31 mentions", pct: 85, quote: "App locks me out after updating. Same loop every time." },
  { name: "App Store", count: "12 mentions", pct: 52, quote: "Can't sign in on 4.7.8. Force-closing and retrying." },
  { name: "X / Twitter", count: "4 mentions", pct: 20, quote: "@app_is_down help my login just cycles forever" },
  { name: "YouTube", count: "0 mentions", pct: 3, quote: "— no mentions this window —" },
];

const FEATURES = [
  { icon: "⊕", title: "Cross-channel correlation", desc: "The same complaint from Play, App Store, X and YouTube collapses into one signal — with the evidence trail attached." },
  { icon: "◷", title: "Daily 6am digest", desc: "Slack + email. Three to five items, prioritized. No dashboard to visit, no notifications to triage." },
  { icon: "⌥", title: "Conversational Q&A", desc: "Ask 'what are iOS users saying about onboarding?' and get a dated, cited answer in seconds." },
  { icon: "↗", title: "Sentiment trend alerts", desc: "Week-over-week, per channel, per feature. We ping you the moment a trend turns." },
  { icon: "⤴", title: "Linear & Jira export", desc: "One click. Ticket pre-filled with the signal, the verbatim quotes, and the channels it came from." },
  { icon: "◉", title: "Public channels, today", desc: "Play, App Store, X, YouTube. Reddit and Zendesk in open beta this quarter." },
];

const FOOTER_COLS = [
  { head: "PRODUCT", items: ["Features", "Channels", "Pricing", "Changelog"] },
  { head: "RESOURCES", items: ["Docs", "API", "Security", "Status"] },
  { head: "COMPANY", items: ["About", "Blog", "Careers", "Contact"] },
  { head: "LEGAL", items: ["Privacy", "Terms", "DPA"] },
];

export default function MarketingPage() {
  const revealRefs = useRef<HTMLElement[]>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add(s.visible);
            observer.unobserve(e.target);
          }
        });
      },
      { threshold: 0.1 }
    );
    revealRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const addReveal = (el: HTMLElement | null) => {
    if (el && !revealRefs.current.includes(el)) revealRefs.current.push(el);
  };

  return (
    <div className={s.page}>
      {/* NAV */}
      <nav className={s.nav}>
        <div className={s.navLeft}>
          <a href="#" className={s.logo}>
            <span className={s.logoDot} />
            Rivue
          </a>
          <ul className={s.navLinks}>
            {["Product", "Channels", "Pricing", "Changelog", "Docs"].map((l) => (
              <li key={l}><a href="#">{l}</a></li>
            ))}
          </ul>
        </div>
        <div className={s.navRight}>
          <a href="/auth" className={s.navSignIn}>Sign in</a>
          <a href="/auth" className={s.btnPrimarySm}>Start free →</a>
        </div>
      </nav>

      {/* HERO */}
      <section className={s.hero}>
        <div className={s.heroInner}>
          <div className={s.heroContent}>
            <div className={s.sectionLabel}>
              <span className={s.num}>§01</span>
              The product · For PMs who ship fast
            </div>
            <h1 className={s.heroH1}>
              Five tabs of chaos.<br />
              <em>One morning digest.</em>
            </h1>
            <p className={s.heroLede}>
              Rivue reads every public channel your users talk on — Play, App&nbsp;Store,
              YouTube, X, Reddit — and hands you the one thing to fix before standup.
            </p>
            <div className={s.heroCtas}>
              <a href="/auth" className={s.btnPrimaryLg}>Start free · 60s</a>
              <button className={s.btnGhostLg}>See a real digest →</button>
            </div>
            <div className={s.heroTrust}>
              <span>Free forever for 1 app</span>
              <span>·</span>
              <span>No credit card</span>
              <span>·</span>
              <span>Ships to Slack + email</span>
            </div>
          </div>
        </div>
      </section>

      {/* BEFORE / AFTER */}
      <section className={s.splitSection}>
        <div className={s.splitInner}>
          {/* Before */}
          <div ref={addReveal} className={s.reveal}>
            <div className={s.splitLabel}>BEFORE · 08:42 AM · BROWSER</div>
            <div className={s.browserChrome}>
              <div className={s.browserBar}>
                <div className={s.browserDots}>
                  <span className={s.browserDot} style={{ background: "#e7685a" }} />
                  <span className={s.browserDot} style={{ background: "#f0b42e" }} />
                  <span className={s.browserDot} style={{ background: "#5ab55e" }} />
                </div>
                <div className={s.browserTabs}>
                  {TABS.map((t, i) => (
                    <div key={t} className={i === 0 ? s.browserTabActive : s.browserTab}>
                      <span className={s.tabDot} />
                      <span className={s.tabName}>{t}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className={s.urlBar}>
                <span className={s.urlNavArrows}>◀ ▶</span>
                <span className={s.urlAddress}>play.google.com/console/reviews</span>
              </div>
              <div className={s.browserContent}>
                <div className={s.reviewsHeader}>
                  <span className={s.reviewsHeaderLabel}>NEW REVIEWS · LAST 48H</span>
                  <span className={s.reviewsTrend}>↓ 0.3★ WoW</span>
                </div>
                <div className={s.reviewList}>
                  {REVIEWS.map((r, i) => (
                    <div key={i} className={s.reviewItem}>
                      <span className={s.reviewStars}>{r.stars}</span>
                      {r.text}
                    </div>
                  ))}
                </div>
              </div>
              <div className={s.browserFooter}>
                6 OF 847 NEW · 12 MIN TO TRIAGE · 4 OTHER TABS STILL OPEN
              </div>
            </div>
            <p className={s.splitCaption}>
              + 4 more tabs open. + 3 Slack threads. + 1 shared doc nobody reads.
              The same complaint said five ways, in five places.
            </p>
          </div>

          {/* After */}
          <div ref={addReveal} className={s.reveal} style={{ transitionDelay: "0.12s" }}>
            <div className={s.splitLabelTeal}>AFTER · 06:00 AM · INBOX</div>
            <div className={s.digestCard}>
              <div className={s.digestHeader}>
                <div className={s.digestHeaderLeft}>
                  <span className={s.digestTealDot} />
                  <span className={s.digestBrand}>RIVUE · TUE 06:00</span>
                </div>
                <span className={s.digestNum}>№ 247</span>
              </div>
              <div className={s.digestBody}>
                <div className={s.digestEyebrow}>DAILY DIGEST · TUE APR 14</div>
                <div className={s.digestTitle}>3 things that need you today.</div>
                <div className={s.signals}>
                  {SIGNALS.map((sig) => (
                    <div key={sig.label} className={s.signalItem}>
                      <span className={`${s.signalDot} ${s[sig.tone]}`} />
                      <div className={s.signalContent}>
                        <div className={s.signalLabel}>{sig.label}</div>
                        <div className={s.signalTitle}>{sig.title}</div>
                        <div className={s.signalMeta}>{sig.meta}</div>
                      </div>
                      <span className={s.signalTrend}>{sig.trend}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className={s.digestFooter}>
                <span className={s.digestFooterNote}>→ 23 more signals filed, no action needed</span>
                <span className={s.digestFooterLink}>Open full report →</span>
              </div>
            </div>
            <p className={s.splitCaption}>
              Same morning. The 847 reviews, the four channels, the Slack noise —
              collapsed into the three items that will move the roadmap today.
            </p>
          </div>
        </div>
      </section>

      {/* METRICS */}
      <div className={s.metrics}>
        <div className={s.metricsGrid}>
          {[
            { val: "6:00 AM", label: "In your inbox daily", desc: "Slack + email. Before the first tab opens." },
            { val: "4 CHANNELS", label: "Correlated into one signal", desc: "Play, App Store, YouTube, X. Reddit + Zendesk in beta." },
            { val: "1 CLICK", label: "Linear / Jira export", desc: "With the full evidence trail attached." },
          ].map((m, i) => (
            <div key={i} className={s.metricItem} ref={addReveal as never}>
              <div className={s.metricValue}>{m.val}</div>
              <div className={s.metricLabel}>{m.label}</div>
              <div className={s.metricDesc}>{m.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* CORRELATION */}
      <section className={s.correlation}>
        <div className={s.correlationInner}>
          <div ref={addReveal} className={s.reveal}>
            <div className={s.sectionLabel}>
              <span className={s.num}>§02</span>
              The core idea
            </div>
            <h2 className={s.correlationH2}>
              One bug. Four channels.<br />
              <em>One signal.</em>
            </h2>
            <p className={s.correlationBody}>
              Other tools dump reviews into a dashboard and hope you&apos;ll read them. Rivue
              watches for the same complaint surfacing in different places — and fuses it
              into one weighted signal, ranked by urgency.
            </p>
            <p className={s.correlationBody}>
              You get a ranked list. Not 47 tickets. Not a wordcloud. A list — with the
              evidence attached.
            </p>
          </div>

          <div ref={addReveal} className={`${s.reveal} ${s.clusterCard}`} style={{ transitionDelay: "0.1s" }}>
            <div className={s.clusterHeader}>
              <span className={s.clusterHeaderLabel}>SIGNAL CLUSTER · LIVE</span>
              <span className={s.clusterLive}>
                <span className={s.clusterLiveDot} />
                CORRELATING
              </span>
            </div>
            <div className={s.channelList}>
              {CHANNELS.map((ch) => (
                <div key={ch.name} className={s.channelItem}>
                  <div className={s.channelTop}>
                    <span className={s.channelName}>{ch.name}</span>
                    <span className={s.channelCount}>{ch.count}</span>
                  </div>
                  <div className={s.channelBar}>
                    <div className={s.channelBarFill} style={{ width: `${ch.pct}%` }} />
                  </div>
                  <div className={s.channelQuote}>&ldquo;{ch.quote}&rdquo;</div>
                </div>
              ))}
            </div>
            <div className={s.clusterFooter}>
              <span className={s.clusterFooterDot} />
              <span className={s.clusterFooterText}>Login loop — 47 mentions</span>
              <span className={s.clusterFooterRank}>RANK #1 · TODAY</span>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className={s.features}>
        <div className={s.featuresInner}>
          <div className={s.sectionLabel}>
            <span className={s.num}>§03</span>
            What&apos;s inside
          </div>
          <h2 className={s.featuresH2}>Everything PMs actually need.</h2>
          <div className={s.featuresGrid}>
            {FEATURES.map((f) => (
              <div key={f.title} className={s.featureCard}>
                <div className={s.featureIcon}>{f.icon}</div>
                <div className={s.featureTitle}>{f.title}</div>
                <div className={s.featureDesc}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIAL */}
      <section className={s.testimonial}>
        <div ref={addReveal} className={`${s.testimonialInner} ${s.reveal}`}>
          <blockquote className={s.testimonialQuote}>
            &ldquo;I used to start Tuesdays with{" "}
            <em>five tabs and a panic attack</em>. Now I open one email and I already
            know what to tell the team.&rdquo;
          </blockquote>
          <div className={s.testimonialAttrib}>
            <div className={s.testimonialAvatar} />
            <div>
              <div className={s.testimonialName}>Maya Chen</div>
              <div className={s.testimonialRole}>Head of Product · Kindling</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={s.cta}>
        <div className={s.ctaInner}>
          <div ref={addReveal} className={s.reveal}>
            <div className={s.sectionLabel}>
              <span className={s.num}>§04</span>
              Start
            </div>
            <h2 className={s.ctaH2}>
              Your Tuesday morning,<br />
              <em>re-engineered.</em>
            </h2>
            <p className={s.ctaBody}>
              Free forever for one app. Sixty-second setup. No credit card. Your first
              digest lands tomorrow at 6am.
            </p>
            <div className={s.ctaCtas}>
              <a href="/auth" className={s.btnPrimaryLg}>Start free →</a>
              <button className={s.btnGhostLg}>Book a walkthrough</button>
            </div>
          </div>

          <div ref={addReveal} className={`${s.reveal} ${s.ctaCard}`} style={{ transitionDelay: "0.1s" }}>
            <div className={s.ctaCardTitle}>WHAT YOU&apos;LL GET TOMORROW MORNING</div>
            <ul className={s.ctaList}>
              <li>A ranked list of 3–5 things that need you today</li>
              <li>Every item with verbatim quotes and the channels they came from</li>
              <li>One-click export to Linear or Jira</li>
              <li>A weekly sentiment summary, Mondays at 6am</li>
            </ul>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className={s.footer}>
        <div className={s.footerInner}>
          <div className={s.footerGrid}>
            <div>
              <a href="#" className={s.logo}>
                <span className={s.logoDot} />
                Rivue
              </a>
              <p className={s.footerDesc}>
                The morning digest of what your users actually said — across every
                public channel.
              </p>
            </div>
            {FOOTER_COLS.map((col) => (
              <div key={col.head}>
                <div className={s.footerColHead}>{col.head}</div>
                <div className={s.footerLinks}>
                  {col.items.map((item) => (
                    <a key={item} href="#">{item}</a>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className={s.footerBottom}>
            <span className={s.footerMono}>© 2025 Rivue Labs · Made for PMs who ship</span>
            <span>Built in SF + NYC</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
