import { useEffect, useState } from "react";
import { money, type Result } from "../services/api";
export default function TransactionReview({
  proposal,
  busy,
  onConfirm,
  onCancel,
}: {
  proposal: Result | null;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!proposal?.transaction || !proposal.intent_id) return null;
  const t = proposal.transaction,
    expired = t.expires_at * 1000 <= now;
  return (
    <section className="panel review-panel">
      <div className="eyebrow">
        FINANCIAL INTENT LOCK <span>⌑</span>
      </div>
      <h3>Review exact payment</h3>
      <div className="transfer-amount">{money(t.amount_minor, t.currency)}</div>
      <dl>
        <div>
          <dt>Beneficiary</dt>
          <dd>{t.beneficiary_name}</dd>
        </div>
        <div>
          <dt>Account</dt>
          <dd>{t.masked_account}</dd>
        </div>
        <div>
          <dt>From</dt>
          <dd>{t.source_account}</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>{new Date(t.expires_at * 1000).toLocaleTimeString()}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{expired ? "EXPIRED" : t.status}</dd>
        </div>
      </dl>
      {t.status === "PENDING_CONFIRMATION" ? (
        <div className="review-actions">
          <button
            className="primary"
            disabled={busy || expired}
            onClick={onConfirm}
          >
            {busy ? "Verifying…" : "Confirm & execute"}
          </button>
          <button disabled={busy} onClick={onCancel}>
            Cancel
          </button>
        </div>
      ) : (
        <p className="muted">
          {t.status === "EXECUTED"
            ? "Payment completed through the independent guard."
            : "Proposal is no longer pending."}
        </p>
      )}
      <p className="small muted">
        Only the signed details above can reach the mock bank.
      </p>
    </section>
  );
}
