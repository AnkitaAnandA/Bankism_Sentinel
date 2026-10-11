import { useEffect, useState, type ReactNode } from "react";
import { CheckCircle2, Clock3, LockKeyhole } from "lucide-react";
import { money, type Result } from "../services/api";
import {
  AnimatedMoney,
  Badge,
  Button,
  KeyValue,
  Stepper,
  Tooltip,
} from "../ui";
import { humanize, maskAccount } from "../ui/format";
export default function TransactionReview({
  proposal,
  busy,
  onConfirm,
  onCancel,
  newBalance,
  previousBalance,
}: {
  proposal: Result | null;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  newBalance?: number;
  previousBalance?: number;
}) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  if (!proposal?.transaction || !proposal.intent_id) return null;
  const t = proposal.transaction;
  const pending = t.status === "PENDING_CONFIRMATION";
  const confirmed = t.status === "CONFIRMED";
  const executed = t.status === "EXECUTED";
  const seconds = Math.max(0, Math.ceil((t.expires_at * 1000 - now) / 1000));
  const expired = (pending || confirmed) && seconds === 0;
  return (
    <section
      className={`review-panel ${executed ? "receipt" : ""}`}
      aria-label={executed ? "Payment receipt" : "Payment review"}
    >
      <div className="panel-heading">
        <h3 className="inline">
          {executed ? (
            <CheckCircle2 size={19} aria-hidden="true" />
          ) : (
            <LockKeyhole size={19} aria-hidden="true" />
          )}
          {executed
            ? "Payment complete"
            : pending || confirmed
              ? "Review your payment"
              : "Payment proposal closed"}
        </h3>
        <Badge tone={executed ? "allow" : expired ? "block" : "review"}>
          {expired ? "Expired" : humanize(t.status)}
        </Badge>
      </div>
      <Stepper
        active={executed ? 3 : confirmed ? 2 : 1}
        terminal={
          expired
            ? "Expired"
            : t.status === "CANCELLED"
              ? "Cancelled"
              : undefined
        }
      />
      <div className="review-summary">
        <div>
          <span className="muted small">Sending to {t.beneficiary_name}</span>
          <div className="transfer-amount">
            {money(t.amount_minor, t.currency)}
          </div>
        </div>
        <span className="payee-avatar" aria-hidden="true">
          {t.beneficiary_name.slice(0, 1)}
        </span>
      </div>
      <KeyValue
        rows={[
          [
            "Payee account",
            <span className="mono">{maskAccount(t.masked_account)}</span>,
          ],
          ["Source account", humanize(t.source_account)],
          ["Currency", t.currency],
          ...(executed && t.transaction_id
            ? [
                [
                  "Transaction ID",
                  <span className="mono break">{t.transaction_id}</span>,
                ] as [string, ReactNode],
              ]
            : []),
          ...(executed && newBalance !== undefined
            ? [
                [
                  "New available balance",
                  <strong className="balance-receipt">
                    <AnimatedMoney
                      value={newBalance}
                      from={previousBalance}
                      currency={t.currency}
                    />
                  </strong>,
                ] as [string, ReactNode],
              ]
            : []),
        ]}
      />
      <div className="review-security">
        <Tooltip text="The server verified and locked these exact details when it prepared the proposal. Confirmation and execution independently recheck the lock.">
          <span className="inline">
            <LockKeyhole size={14} aria-hidden="true" />
            Integrity lock verified at preparation
          </span>
        </Tooltip>
        {(pending || confirmed) && (
          <span
            className="inline countdown"
            role="timer"
            aria-label="Payment expiry"
          >
            <Clock3 size={14} aria-hidden="true" />
            {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}{" "}
            remaining
          </span>
        )}
      </div>
      {expired ? (
        <p className="expiry-note" role="status">
          This proposal has expired. Send a new request to prepare a fresh
          payment.
        </p>
      ) : pending ? (
        <div className="review-actions">
          <Button variant="primary" loading={busy} onClick={onConfirm}>
            Confirm & send
          </Button>
          <Button onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        </div>
      ) : confirmed ? (
        <div className="review-actions">
          <Button variant="primary" loading={busy} onClick={onConfirm}>
            Retry guarded execution
          </Button>
          <p className="small muted">
            Consent is recorded. A retry uses the same payment and idempotency
            key.
          </p>
        </div>
      ) : (
        <p className="small muted">
          {executed
            ? "Executed once through the independent guard. No further confirmation is needed."
            : t.status === "CANCELLED"
              ? "Cancelled. No money was moved."
              : "This proposal no longer accepts confirmation."}
        </p>
      )}
    </section>
  );
}
