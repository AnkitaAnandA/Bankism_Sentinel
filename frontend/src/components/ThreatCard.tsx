import { memo } from "react";
import {
  CheckCircle2,
  CircleX,
  ShieldCheck,
  ShieldAlert,
  CircleHelp,
} from "lucide-react";
import type { Result } from "../services/api";
import { Badge, Card, CodeBlock, EmptyState } from "../ui";
import { humanize } from "../ui/format";
export default memo(function ThreatCard({
  result,
  compact = false,
}: {
  result: Result | null;
  compact?: boolean;
}) {
  if (!result)
    return (
      <Card>
        <EmptyState
          title="Your verdict will appear here"
          description="Inspect a request to see its decision, risk and policy evidence."
        />
      </Card>
    );
  const Icon =
    result.verdict === "ALLOW"
      ? ShieldCheck
      : result.verdict === "BLOCK"
        ? ShieldAlert
        : CircleHelp;
  const title =
    result.verdict === "BLOCK"
      ? "We couldn’t process this request"
      : result.requires_confirmation
        ? "Ready for your review"
        : result.verdict === "REVIEW"
          ? "A little more detail, please"
          : "Request checked";
  return (
    <Card
      className={`verdict-card ${result.verdict.toLowerCase()} ${compact ? "compact" : ""}`}
    >
      <div className="verdict-heading">
        <span className="verdict-icon">
          <Icon size={20} aria-hidden="true" />
        </span>
        <Badge tone={result.verdict}>{result.verdict}</Badge>
        <Badge tone={result.risk_level}>
          {humanize(result.risk_level)} risk
        </Badge>
      </div>
      <h3>{title}</h3>
      <p className="verdict-reason">{result.reason}</p>
      <div className="verdict-category">
        {result.threat_category === "NONE"
          ? "No threat detected"
          : humanize(result.threat_category)}
      </div>
      <details className="technical">
        <summary>Technical details</summary>
        <div className="checks">
          {Object.entries(result.policy_checks).map(([key, passed]) => (
            <div key={key}>
              {passed ? (
                <CheckCircle2 size={16} className="pass" aria-hidden="true" />
              ) : (
                <CircleX size={16} className="fail" aria-hidden="true" />
              )}
              <span>{humanize(key)}</span>
              <strong>{passed ? "Pass" : "Not passed"}</strong>
            </div>
          ))}
        </div>
        <div className="small muted">
          Request ID <span className="mono break">{result.request_id}</span>
        </div>
        <p className="small muted">Classifier: {result.classifier_mode}</p>
        <CodeBlock value={result} />
      </details>
    </Card>
  );
});
