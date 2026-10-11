import { useCallback, useEffect, useRef, useState } from "react";
import { FlaskConical, RefreshCw, ShieldCheck } from "lucide-react";
import SecurityTimeline from "../components/SecurityTimeline";
import { api, type Evaluation, type Result, type Event } from "../services/api";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  Stat,
  Tabs,
} from "../ui";
import { humanize } from "../ui/format";
import { averageAnalyzeLatency, analyzeSampleCount } from "../ui/measurements";
function VerdictChart({ events }: { events: Event[] }) {
  if (!events.length)
    return (
      <EmptyState
        title="No events to chart"
        description="Verdict history will appear after requests are inspected."
      />
    );
  const sorted = [...events].sort((a, b) => a.timestamp - b.timestamp);
  const start = sorted[0].timestamp;
  const duration = Math.max(1, sorted[sorted.length - 1].timestamp - start);
  const bins = Array.from({ length: 6 }, () => ({
    ALLOW: 0,
    REVIEW: 0,
    BLOCK: 0,
  }));
  sorted.forEach(
    (event) =>
      bins[Math.min(5, Math.floor(((event.timestamp - start) / duration) * 6))][
        event.verdict
      ]++,
  );
  const max = Math.max(
    1,
    ...bins.map((bin) => bin.ALLOW + bin.REVIEW + bin.BLOCK),
  );
  const colors = {
    ALLOW: "var(--allow-fg)",
    REVIEW: "var(--review-fg)",
    BLOCK: "var(--block-fg)",
  };
  const counts = sorted.reduce(
    (acc, event) => ({ ...acc, [event.verdict]: acc[event.verdict] + 1 }),
    { ALLOW: 0, REVIEW: 0, BLOCK: 0 },
  );
  return (
    <>
      <svg
        role="img"
        aria-label={`Latest ${events.length} events over six time intervals: ${counts.ALLOW} allowed, ${counts.REVIEW} review, ${counts.BLOCK} blocked.`}
        viewBox="0 0 460 150"
      >
        <line x1="16" y1="125" x2="444" y2="125" stroke="var(--border)" />
        {bins.map((bin, i) => {
          let y = 125;
          return (
            <g key={i}>
              {(["ALLOW", "REVIEW", "BLOCK"] as const).map((verdict) => {
                const height = (bin[verdict] / max) * 100;
                y -= height;
                return (
                  <rect
                    key={verdict}
                    x={30 + i * 71}
                    y={y}
                    width="36"
                    height={height}
                    rx="3"
                    fill={colors[verdict]}
                  />
                );
              })}
              <text
                x={48 + i * 71}
                y="146"
                textAnchor="middle"
                fill="var(--text-muted)"
                fontSize="10"
              >
                {i + 1}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="chart-legend">
        {(["ALLOW", "REVIEW", "BLOCK"] as const).map((verdict) => (
          <span key={verdict}>
            <i style={{ background: colors[verdict] }} />
            {humanize(verdict)} {counts[verdict]}
          </span>
        ))}
      </div>
    </>
  );
}
export default function Dashboard({ analyst }: { analyst: boolean }) {
  const [data, setData] = useState<Result | null>(null),
    [metrics, setMetrics] = useState<Result | null>(null),
    [offset, setOffset] = useState(0),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [filter, setFilter] = useState("all"),
    [query, setQuery] = useState(""),
    [evaluation, setEvaluation] = useState<Evaluation | null>(null),
    [evaluating, setEvaluating] = useState(false);
  const running = useRef(false);
  const load = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      const [events, counts] = await Promise.all([
        api(`/api/security/events?offset=${offset}&limit=20`),
        api("/api/security/metrics"),
      ]);
      if (events.verdict === "BLOCK" || counts.verdict === "BLOCK")
        throw new Error(events.reason || counts.reason);
      setData(events);
      setMetrics(counts);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [offset]);
  useEffect(() => {
    if (analyst) void load();
  }, [analyst, load]);
  async function evaluate() {
    if (running.current) return;
    running.current = true;
    setEvaluating(true);
    setError("");
    try {
      const result = await api("/api/security/evaluate", {});
      if (!result.evaluation.length) throw new Error(result.reason);
      setEvaluation(result.evaluation[2]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      running.current = false;
      setEvaluating(false);
    }
  }
  if (!analyst)
    return (
      <Card>
        <EmptyState
          title="Analyst access required"
          description="Choose the Security Analyst demo identity to inspect protected events."
        />
      </Card>
    );
  const counts = metrics?.metrics;
  const categories = Object.entries(counts?.categories || {})
    .filter(([category]) => category !== "NONE")
    .sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...categories.map(([, count]) => count));
  const filtered = (data?.events || []).filter(
    (event) =>
      (filter === "all" || event.verdict.toLowerCase() === filter) &&
      `${event.category} ${event.evidence} ${event.request_id}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const latency = averageAnalyzeLatency();
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SECURITY OPERATIONS</div>
          <h1>A clear view of the boundary.</h1>
          <p>
            Inspect decisions, trace the evidence, and verify financial
            containment.
          </p>
        </div>
        <Button onClick={() => void load()} loading={busy}>
          <RefreshCw size={16} aria-hidden="true" />
          Refresh events
        </Button>
      </div>
      {error && <ErrorState message={error} />}
      <div className="stats-grid">
        <Stat
          label="Requests inspected"
          value={counts?.total ?? "—"}
          note="All audited API requests"
        />
        <Stat
          label="Blocked"
          value={counts?.block ?? "—"}
          note="Rejected requests"
        />
        <Stat
          label="Needs review"
          value={counts?.review ?? "—"}
          note="Consent or clarification"
        />
        <Stat
          label="Allowed"
          value={counts?.allow ?? "—"}
          note="Approved decisions"
        />
        <Stat
          label="Unauthorized executions"
          value={evaluation?.unauthorized_transfers ?? "—"}
          note={
            evaluation ? "Isolated evaluation only" : "Run containment check"
          }
          tone="highlight"
        />
        <Stat
          label="Avg. analyze round trip"
          value={latency === null ? "—" : `${latency} ms`}
          note={
            latency === null
              ? "Inspect a request in Attack Lab"
              : `${analyzeSampleCount()} browser samples · this session`
          }
        />
      </div>
      <div className="containment-callout">
        <div>
          <strong className="inline">
            <ShieldCheck size={18} aria-hidden="true" />
            Authorization is checked independently
          </strong>
          <p>
            {evaluation
              ? `${evaluation.dataset_size} synthetic cases evaluated. ${evaluation.unauthorized_transfers} unauthorized sandbox transfers; ${(evaluation.tamper_rejection * 100).toFixed(0)}% tamper rejection. This is not a live ledger metric.`
              : "Run the isolated suite to verify containment. The live API does not expose an unauthorized-ledger aggregate."}
          </p>
        </div>
        <Button onClick={() => void evaluate()} loading={evaluating}>
          <FlaskConical size={16} aria-hidden="true" />
          Verify containment
        </Button>
      </div>
      <div className="charts-grid">
        <Card className="chart">
          <h2>Verdicts over time</h2>
          <p>Latest loaded audit page · six equal time intervals</p>
          <VerdictChart events={data?.events || []} />
        </Card>
        <Card className="chart">
          <h2>Threat categories</h2>
          <p>All audited requests · no-threat decisions excluded</p>
          {categories.length ? (
            categories.slice(0, 6).map(([category, count]) => (
              <div className="category-bar" key={category}>
                <span>{humanize(category)}</span>
                <strong>{count}</strong>
                <div>
                  <i style={{ width: `${(count / max) * 100}%` }} />
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              title="No threats recorded"
              description="Threat categories populate when the firewall detects suspicious requests."
            />
          )}
        </Card>
      </div>
      <Card>
        <div className="panel-heading">
          <div>
            <h2>Security timeline</h2>
            <p className="small muted">
              Redacted evidence. Select an ID to inspect the complete event.
            </p>
          </div>
          <Badge tone="info">Analyst access</Badge>
        </div>
        <div className="event-filters">
          <Tabs
            value={filter}
            onChange={setFilter}
            items={[
              { id: "all", label: "All decisions" },
              { id: "block", label: "Blocked" },
              { id: "review", label: "Review" },
              { id: "allow", label: "Allowed" },
            ]}
          />
          <Input
            aria-label="Filter events on this page"
            placeholder="Search this page…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <p className="caption muted" style={{ marginBottom: 12 }}>
          Showing {filtered.length} of {data?.events.length ?? 0} loaded events
          · page {offset / 20 + 1}
        </p>
        <SecurityTimeline events={filtered} />
        <div className="pagination">
          <Button
            disabled={offset === 0 || busy}
            onClick={() => setOffset(Math.max(0, offset - 20))}
          >
            Previous
          </Button>
          <span>Page {offset / 20 + 1}</span>
          <Button
            disabled={(data?.events.length ?? 0) < 20 || busy}
            onClick={() => setOffset(offset + 20)}
          >
            Next
          </Button>
        </div>
      </Card>
      <p className="metric-explainer">
        Analyze timing is measured in this browser, including network overhead.
        Audited request counts also include session and account endpoints.
      </p>
    </>
  );
}
