"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Step = 0 | 1 | 2 | 3;
type SourceId = "playstore" | "appstore" | "x";
type PreviewStatus = "idle" | "loading" | "success" | "error";

type PreviewData = {
  source: SourceId | string;
  name?: string;
  developer?: string;
  icon?: string;
  avatar?: string;
  rating?: number | null;
  reviews?: number | null;
  installs?: string | null;
  category?: string | null;
  version?: string | null;
  username?: string;
  followers?: number | null;
  tweet_count?: number | null;
  mentions_7d?: number | null;
  verified?: boolean;
  status?: string;
  delight?: string;
};

type PreviewState = {
  status: PreviewStatus;
  data?: PreviewData;
  error?: string;
};

type SourceConfig = {
  id: SourceId;
  label: string;
  title: string;
  prompt: string;
  placeholder: string;
  endpoint: string;
  sample: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const sources: SourceConfig[] = [
  {
    id: "playstore",
    label: "Play Store",
    title: "Android app",
    prompt: "Paste a Google Play link and we will verify the app instantly.",
    placeholder: "https://play.google.com/store/apps/details?id=com.smartspends",
    endpoint: "/api/preview/playstore",
    sample: "https://play.google.com/store/apps/details?id=com.smartspends",
  },
  {
    id: "appstore",
    label: "App Store",
    title: "iOS app",
    prompt: "Paste an App Store link and we will pull the public listing.",
    placeholder: "https://apps.apple.com/in/app/et-money/id1212752482",
    endpoint: "/api/preview/appstore",
    sample: "https://apps.apple.com/in/app/et-money/id1212752482",
  },
  {
    id: "x",
    label: "X",
    title: "Social signal",
    prompt: "Paste an X profile URL and we will check followers plus recent mentions.",
    placeholder: "https://x.com/ETMONEY",
    endpoint: "/api/preview/x",
    sample: "https://x.com/ETMONEY",
  },
];

const stepMeta = [
  { eyebrow: "Start", title: "Name the workspace" },
  { eyebrow: "Connect", title: "Light up your channels" },
  { eyebrow: "Tune", title: "Set the baseline" },
  { eyebrow: "Ready", title: "First report queued" },
];

export default function Home() {
  const [step, setStep] = useState<Step>(0);
  const [company, setCompany] = useState("Acme Corp");
  const [activeSource, setActiveSource] = useState<SourceId>("playstore");
  const [market, setMarket] = useState("India");
  const [lookback, setLookback] = useState("Last 30 days");
  const [values, setValues] = useState<Record<SourceId, string>>({
    playstore: "",
    appstore: "",
    x: "",
  });
  const [previews, setPreviews] = useState<Record<SourceId, PreviewState>>({
    playstore: { status: "idle" },
    appstore: { status: "idle" },
    x: { status: "idle" },
  });

  const activeConfig = sources.find((source) => source.id === activeSource) ?? sources[0];
  const completedSources = sources.filter((source) => previews[source.id].status === "success");
  const sourceScore = completedSources.length;
  const canFinish = sourceScore > 0;

  function goTo(nextStep: Step) {
    setStep(nextStep);
  }

  function next() {
    setStep((current) => Math.min(current + 1, 3) as Step);
  }

  function back() {
    setStep((current) => Math.max(current - 1, 0) as Step);
  }

  function submitWelcome(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    next();
  }

  function updateSource(id: SourceId, value: string) {
    setValues((current) => ({ ...current, [id]: value }));
    setActiveSource(id);
  }

  function useSample(id: SourceId) {
    const source = sources.find((item) => item.id === id);
    if (!source) return;
    updateSource(id, source.sample);
  }

  useEffect(() => {
    const controllers: AbortController[] = [];

    sources.forEach((source) => {
      const rawValue = values[source.id].trim();
      if (rawValue.length < 3) {
        setPreviews((current) => ({
          ...current,
          [source.id]: { status: "idle" },
        }));
        return;
      }

      setPreviews((current) => ({
        ...current,
        [source.id]: { status: "loading", data: current[source.id].data },
      }));

      const controller = new AbortController();
      controllers.push(controller);

      const timeout = window.setTimeout(async () => {
        try {
          const response = await fetch(
            `${API_BASE}${source.endpoint}?url=${encodeURIComponent(rawValue)}`,
            { signal: controller.signal },
          );
          const payload = await response.json();

          if (!response.ok) {
            throw new Error(payload.detail ?? "Could not verify this source yet.");
          }

          setPreviews((current) => ({
            ...current,
            [source.id]: { status: "success", data: payload },
          }));
        } catch (error) {
          if (controller.signal.aborted) return;
          setPreviews((current) => ({
            ...current,
            [source.id]: {
              status: "error",
              error: error instanceof Error ? error.message : "Could not verify this source yet.",
            },
          }));
        }
      }, 650);

      controller.signal.addEventListener("abort", () => window.clearTimeout(timeout));
    });

    return () => {
      controllers.forEach((controller) => controller.abort());
    };
  }, [values]);

  const liveMoments = useMemo(() => {
    const moments = completedSources.map((source) => {
      const preview = previews[source.id].data;
      return `${source.label} verified${preview?.name ? `: ${preview.name}` : ""}`;
    });

    if (previews.x.status === "success") {
      const count = previews.x.data?.mentions_7d;
      moments.push(
        count === null || count === undefined
          ? "X profile connected; mention count needs elevated access"
          : `${formatNumber(count)} recent X mentions mapped`,
      );
    }

    if (!moments.length) {
      return ["Paste a source URL to see the first live signal."];
    }

    return moments.slice(-4);
  }, [completedSources, previews]);

  return (
    <main className="desktop-shell">
      <aside className="rail">
        <div className="brand-lockup">
          <div className="brand-mark">FI</div>
          <div>
            <p>Feedback Intelligence</p>
            <span>Onboarding</span>
          </div>
        </div>

        <nav className="step-list" aria-label="Onboarding steps">
          {stepMeta.map((item, index) => (
            <button
              className={step === index ? "current" : step > index ? "complete" : ""}
              key={item.title}
              onClick={() => goTo(index as Step)}
              type="button"
            >
              <span>{index + 1}</span>
              <div>
                <small>{item.eyebrow}</small>
                <strong>{item.title}</strong>
              </div>
            </button>
          ))}
        </nav>

        <div className="signal-card">
          <p>Live setup score</p>
          <strong>{sourceScore}/3 sources</strong>
          <div className="mini-meter">
            <span style={{ width: `${Math.max(8, (sourceScore / 3) * 100)}%` }} />
          </div>
          <small>
            {sourceScore === 0
              ? "No channels verified yet."
              : `${completedSources.map((source) => source.label).join(", ")} ready.`}
          </small>
        </div>
      </aside>

      <section className="workspace">
        <div className="ambient ambient-one" />
        <div className="ambient ambient-two" />

        {step === 0 && (
          <form className="panel intro-panel" onSubmit={submitWelcome}>
            <div className="panel-copy">
              <p className="kicker">Start with one name</p>
              <h1>Turn scattered feedback into a morning signal.</h1>
              <p>
                Create the workspace, connect public channels, and watch each source
                light up before the first report runs.
              </p>
            </div>

            <div className="workspace-card company-card">
              <label>
                <span>Company name</span>
                <input
                  autoFocus
                  onChange={(event) => setCompany(event.target.value)}
                  placeholder="Acme Corp"
                  value={company}
                />
              </label>
              <div className="delight-row good">
                <span />
                <p>{company || "Your workspace"} will get its own connected feedback view.</p>
              </div>
            </div>

            <div className="action-row">
              <button className="primary-button" type="submit">
                Start connecting
              </button>
              <p>No backend account is created yet.</p>
            </div>
          </form>
        )}

        {step === 1 && (
          <section className="panel source-panel">
            <div className="panel-header">
              <div>
                <p className="kicker">Connect public channels</p>
                <h1>Every paste should feel like progress.</h1>
                <p>
                  Add the links you already have. The app pulls public metadata and gives
                  immediate confirmation.
                </p>
              </div>
              <button className="ghost-button" onClick={back} type="button">
                Back
              </button>
            </div>

            <div className="source-grid">
              <div className="source-stack">
                {sources.map((source) => (
                  <SourceInputCard
                    config={source}
                    key={source.id}
                    onSample={() => useSample(source.id)}
                    onSelect={() => setActiveSource(source.id)}
                    onUpdate={(value) => updateSource(source.id, value)}
                    preview={previews[source.id]}
                    selected={activeSource === source.id}
                    value={values[source.id]}
                  />
                ))}
              </div>

              <PreviewStage
                config={activeConfig}
                preview={previews[activeConfig.id]}
                value={values[activeConfig.id]}
              />
            </div>

            <div className="bottom-bar">
              <div>
                <strong>{sourceScore} of 3 sources verified</strong>
                <p>{canFinish ? "You can continue now." : "Verify at least one source to continue."}</p>
              </div>
              <button className="primary-button" disabled={!canFinish} onClick={next} type="button">
                Continue
              </button>
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="panel preference-panel">
            <div className="panel-header">
              <div>
                <p className="kicker">Tune the first report</p>
                <h1>Pick the baseline for the first scan.</h1>
                <p>
                  These defaults shape how much history the first feedback run pulls in.
                </p>
              </div>
              <button className="ghost-button" onClick={back} type="button">
                Back
              </button>
            </div>

            <div className="preference-grid">
              <div className="workspace-card">
                <label>
                  <span>Primary market</span>
                  <select value={market} onChange={(event) => setMarket(event.target.value)}>
                    <option>India</option>
                    <option>United States</option>
                    <option>United Kingdom</option>
                    <option>Singapore</option>
                  </select>
                </label>
              </div>

              <fieldset className="workspace-card choices">
                <legend>Default lookback</legend>
                {["Last 7 days", "Last 30 days", "Custom range"].map((option) => (
                  <label className={lookback === option ? "selected" : ""} key={option}>
                    <input
                      checked={lookback === option}
                      name="lookback"
                      onChange={() => setLookback(option)}
                      type="radio"
                    />
                    <span />
                    {option}
                  </label>
                ))}
              </fieldset>

              <div className="workspace-card summary-card">
                <p>First scan preview</p>
                <h2>{company || "Workspace"}</h2>
                <dl>
                  <div>
                    <dt>Market</dt>
                    <dd>{market}</dd>
                  </div>
                  <div>
                    <dt>Lookback</dt>
                    <dd>{lookback}</dd>
                  </div>
                  <div>
                    <dt>Sources</dt>
                    <dd>{sourceScore}</dd>
                  </div>
                </dl>
              </div>
            </div>

            <div className="moment-list">
              {liveMoments.map((moment) => (
                <div key={moment}>
                  <span />
                  <p>{moment}</p>
                </div>
              ))}
            </div>

            <div className="bottom-bar">
              <div>
                <strong>Baseline ready</strong>
                <p>The first report will start with {lookback.toLowerCase()} of public signal.</p>
              </div>
              <button className="primary-button" onClick={next} type="button">
                Finish setup
              </button>
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="panel done-panel">
            <div className="success-orb">Ready</div>
            <div className="panel-copy centered">
              <p className="kicker">Workspace connected</p>
              <h1>{company || "Your workspace"} is ready for its first report.</h1>
              <p>
                The connected sources are queued. The next screen can become the feedback
                command center when the backend is ready.
              </p>
            </div>

            <div className="launch-grid">
              {completedSources.map((source) => {
                const preview = previews[source.id].data;
                return (
                  <div className="launch-card" key={source.id}>
                    <span>Verified</span>
                    <strong>{preview?.name ?? source.label}</strong>
                    <p>{source.label}</p>
                  </div>
                );
              })}
            </div>

            <button className="primary-button" onClick={() => goTo(1)} type="button">
              Review sources
            </button>
          </section>
        )}
      </section>
    </main>
  );
}

function SourceInputCard({
  config,
  onSample,
  onSelect,
  onUpdate,
  preview,
  selected,
  value,
}: {
  config: SourceConfig;
  onSample: () => void;
  onSelect: () => void;
  onUpdate: (value: string) => void;
  preview: PreviewState;
  selected: boolean;
  value: string;
}) {
  return (
    <article className={`source-input-card ${selected ? "selected" : ""}`} onClick={onSelect}>
      <div className="source-title">
        <div>
          <span className={`status-dot ${preview.status}`} />
          <strong>{config.title}</strong>
        </div>
        <button onClick={onSample} type="button">
          Try sample
        </button>
      </div>
      <p>{config.prompt}</p>
      <input
        onChange={(event) => onUpdate(event.target.value)}
        onFocus={onSelect}
        placeholder={config.placeholder}
        value={value}
      />
      <SourceStatus preview={preview} />
    </article>
  );
}

function SourceStatus({ preview }: { preview: PreviewState }) {
  if (preview.status === "idle") {
    return <small className="status-line">Waiting for a link.</small>;
  }

  if (preview.status === "loading") {
    return <small className="status-line loading">Looking up public details...</small>;
  }

  if (preview.status === "error") {
    return <small className="status-line error">{preview.error}</small>;
  }

  return <small className="status-line success">{preview.data?.status ?? "Verified"}</small>;
}

function PreviewStage({
  config,
  preview,
  value,
}: {
  config: SourceConfig;
  preview: PreviewState;
  value: string;
}) {
  const data = preview.data;

  return (
    <aside className="preview-stage">
      <div className="preview-topline">
        <span>{config.label}</span>
        <strong>{preview.status === "success" ? "Live match" : "Preview"}</strong>
      </div>

      {preview.status === "idle" && (
        <div className="empty-preview">
          <div className="preview-art" />
          <h2>Paste a link to unlock the first moment.</h2>
          <p>{value ? "Keep typing." : config.placeholder}</p>
        </div>
      )}

      {preview.status === "loading" && (
        <div className="loading-preview">
          <div />
          <span />
          <span />
          <span />
        </div>
      )}

      {preview.status === "error" && (
        <div className="empty-preview error-state">
          <div className="preview-art" />
          <h2>That one did not resolve yet.</h2>
          <p>{preview.error}</p>
        </div>
      )}

      {preview.status === "success" && data && (
        <div className="rich-preview">
          <div className="identity-row">
            <ImageBadge src={data.icon ?? data.avatar} label={data.name ?? data.username ?? config.label} />
            <div>
              <h2>{data.name ?? data.username ?? config.label}</h2>
              <p>{data.developer ?? (data.username ? `@${data.username}` : data.category)}</p>
            </div>
          </div>

          <div className="metric-grid">
            {"rating" in data && (
              <Metric label="Rating" value={data.rating ? `${data.rating}/5` : "NA"} />
            )}
            {"reviews" in data && <Metric label="Reviews" value={formatNumber(data.reviews)} />}
            {"installs" in data && <Metric label="Installs" value={data.installs ?? "NA"} />}
            {"followers" in data && <Metric label="Followers" value={formatNumber(data.followers)} />}
            {"tweet_count" in data && <Metric label="All tweets" value={formatNumber(data.tweet_count)} />}
            {"mentions_7d" in data && (
              <Metric label="7 day mentions" value={formatNumber(data.mentions_7d)} />
            )}
          </div>

          <div className="delight-message">
            <span />
            <p>{data.delight ?? "This source is ready."}</p>
          </div>
        </div>
      )}
    </aside>
  );
}

function ImageBadge({ src, label }: { src?: string; label: string }) {
  if (src) {
    return <img alt={`${label} icon`} className="image-badge" src={src} />;
  }

  return <div className="image-badge fallback">{label.slice(0, 2).toUpperCase()}</div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "NA";
  }
  return Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}
