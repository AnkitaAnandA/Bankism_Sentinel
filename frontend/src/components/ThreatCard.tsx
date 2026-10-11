import { memo } from "react";
import type { Result } from "../services/api";
export default memo(function ThreatCard({ result }: { result: Result | null }) {
  if (!result)
    return (
      <section className="panel verdict-panel">
        <div className="eyebrow">LATEST VERDICT</div>
        <div className="empty-icon">◇</div>
        <h3>Ready to inspect</h3>
        <p className="muted">
          Send a request to see its security decision and policy checks.
        </p>
      </section>
    );
  return (
    <section className="panel verdict-panel" aria-live="polite">
      <div className="eyebrow">
        LATEST VERDICT{" "}
        <span className={"badge " + result.verdict.toLowerCase()}>
          {result.verdict}
        </span>
      </div>
      <h3>{result.threat_category.replaceAll("_", " ").toLowerCase()}</h3>
      <p>{result.reason}</p>
      <div className="risk-line">
        <span>Risk level</span>
        <strong>{result.risk_level}</strong>
      </div>
      <div className="checks">
        {Object.entries(result.policy_checks).map(([key, passed]) => (
          <div key={key}>
            <span className={passed ? "check pass" : "check"}>
              {passed ? "✓" : "○"}
            </span>
            {key.replaceAll("_", " ")}
          </div>
        ))}
      </div>
      {result.findings.map((f, i) => (
        <div className="finding" key={i}>
          Analysis view: {f.view}
        </div>
      ))}
      <div className="request-id">
        REQUEST ID
        <br />
        {result.request_id}
      </div>
      <div className="muted small">Classifier: {result.classifier_mode}</div>
    </section>
  );
});
