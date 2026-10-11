import { useCallback, useEffect, useState } from "react";
import SecurityTimeline from "../components/SecurityTimeline";
import { api, type Result } from "../services/api";
export default function Dashboard({ analyst }: { analyst: boolean }) {
  const [data, setData] = useState<Result | null>(null),
    [metrics, setMetrics] = useState<Result | null>(null),
    [offset, setOffset] = useState(0),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      const [e, m] = await Promise.all([
        api(`/api/security/events?offset=${offset}&limit=20`),
        api("/api/security/metrics"),
      ]);
      setData(e);
      setMetrics(m);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [offset]);
  useEffect(() => {
    if (analyst) load();
  }, [analyst, load]);
  if (!analyst)
    return (
      <div className="panel empty">
        <h2>Analyst workspace</h2>
        <p>
          Select the Security analyst demo session to inspect the audit trail.
          Customer sessions cannot access these records.
        </p>
      </div>
    );
  const m = metrics?.metrics;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SECURITY OPERATIONS</div>
          <h1>Every decision, accounted for.</h1>
          <p>Redacted audit evidence from the synthetic banking environment.</p>
        </div>
        <button onClick={load} disabled={busy}>
          {busy ? "Refreshing…" : "Refresh events"}
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="stats-grid">
        {[
          ["Requests inspected", m?.total],
          ["Allowed", m?.allow],
          ["Blocked", m?.block],
          ["Needs review", m?.review],
        ].map(([label, value]) => (
          <div className="panel stat" key={label}>
            <div className="muted">{label}</div>
            <strong>{value ?? "—"}</strong>
          </div>
        ))}
      </div>
      <div className="panel">
        <div className="panel-heading">
          <h2>Security timeline</h2>
          <span className="pill">ANALYST ACCESS</span>
        </div>
        <SecurityTimeline events={data?.events ?? []} />
        <div className="pagination">
          <button
            disabled={offset === 0 || busy}
            onClick={() => setOffset(Math.max(0, offset - 20))}
          >
            Previous
          </button>
          <span>Page {offset / 20 + 1}</span>
          <button
            disabled={(data?.events.length ?? 0) < 20 || busy}
            onClick={() => setOffset(offset + 20)}
          >
            Next
          </button>
        </div>
      </div>
      <section className="panel categories">
        <h2>Threat categories</h2>
        {m &&
          Object.entries(m.categories).map(([category, count]) => (
            <div key={category}>
              <span>{category.replaceAll("_", " ")}</span>
              <strong>{count}</strong>
            </div>
          ))}
      </section>
    </>
  );
}
