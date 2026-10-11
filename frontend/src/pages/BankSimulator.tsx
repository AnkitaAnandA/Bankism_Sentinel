import { useCallback, useEffect, useState } from "react";
import BankingChat, { type ChatEntry } from "../components/BankingChat";
import ThreatCard from "../components/ThreatCard";
import TransactionReview from "../components/TransactionReview";
import { api, money, type Result } from "../services/api";
export default function BankSimulator() {
  const [bank, setBank] = useState<Result | null>(null),
    [latest, setLatest] = useState<Result | null>(null),
    [proposal, setProposal] = useState<Result | null>(null),
    [entries, setEntries] = useState<ChatEntry[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const refresh = useCallback(
    async () => setBank(await api("/api/accounts/balance")),
    [],
  );
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, [refresh]);
  async function send(text: string) {
    setBusy(true);
    setError("");
    try {
      const context =
        proposal?.transaction?.status === "PENDING_CONFIRMATION"
          ? { intent_id: proposal.intent_id }
          : {};
      const result = await api("/api/intents/prepare", {
        message: text,
        context,
      });
      setLatest(result);
      setEntries((old) => [...old, { text, result }].slice(-20));
      if (result.intent_id) setProposal(result);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function confirm(cancel = false) {
    if (!proposal?.transaction || !proposal.intent_id) return;
    setBusy(true);
    setError("");
    try {
      let r = await api(`/api/intents/${proposal.intent_id}/confirm`, {
        integrity_tag: proposal.transaction.integrity_tag,
        action: cancel ? "cancel" : "confirm",
      });
      setLatest(r);
      setProposal(r);
      if (r.approved && !cancel) {
        r = await api("/api/transfers/execute", {
          intent_id: proposal.intent_id,
          idempotency_key: crypto.randomUUID(),
        });
        setLatest(r);
        setProposal(r);
      }
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">BANK SIMULATOR</div>
          <h1>Bank with confidence.</h1>
          <p>Natural language in. Verified financial intent out.</p>
        </div>
        <span className="system-status">
          <span className="status-dot" />
          Guard active
        </span>
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <div className="account-grid">
        {bank?.accounts.map((a) => (
          <div className="account-card" key={a.id}>
            <div>
              {a.name} account <span>{a.masked_account}</span>
            </div>
            <strong>{money(a.balance_minor, a.currency)}</strong>
            <div className="small muted">Synthetic available balance</div>
          </div>
        ))}
        {bank && !bank.accounts.length && (
          <div className="panel muted">
            This demo identity has no customer accounts.
          </div>
        )}
      </div>
      <div className="bank-layout">
        <div>
          <BankingChat entries={entries} busy={busy} onSend={send} />
          <section className="panel activity">
            <div className="panel-heading">
              <h2>Recent activity</h2>
              <span className="muted small">Last 5 transfers</span>
            </div>
            {bank?.history.length ? (
              bank.history.map((t) => (
                <div className="activity-row" key={t.id}>
                  <span>↗</span>
                  <div>
                    To {t.beneficiary_name}
                    <small>
                      {new Date(t.timestamp * 1000).toLocaleString()}
                    </small>
                  </div>
                  <strong>−{money(t.amount_minor, t.currency)}</strong>
                </div>
              ))
            ) : (
              <p className="empty">
                No transfers yet. Your next confirmed payment will appear here.
              </p>
            )}
          </section>
        </div>
        <div className="right-stack">
          <TransactionReview
            proposal={proposal}
            busy={busy}
            onConfirm={() => confirm()}
            onCancel={() => confirm(true)}
          />
          <ThreatCard result={latest} />
          <div className="guard-note">
            <span>⌑</span>
            <div>
              <strong>Detection can fail. Authorization holds.</strong>
              <p>
                The independent guard reloads the locked intent and checks
                consent, integrity, expiry, policy and replay protection.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
