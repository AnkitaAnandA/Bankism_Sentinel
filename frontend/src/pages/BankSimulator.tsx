import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  ChevronDown,
  LockKeyhole,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import BankingChat, { type ChatEntry } from "../components/BankingChat";
import TransactionReview from "../components/TransactionReview";
import { api, money, type Result } from "../services/api";
import { Badge, Card, EmptyState, ErrorState, Skeleton, Toast } from "../ui";
import { humanize, maskAccount, shortTime } from "../ui/format";
export default function BankSimulator({ user }: { user: string }) {
  const [bank, setBank] = useState<Result | null>(null),
    [proposal, setProposal] = useState<Result | null>(null),
    [entries, setEntries] = useState<ChatEntry[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [receiptBalance, setReceiptBalance] = useState<number | undefined>(),
    [previousBalance, setPreviousBalance] = useState<number | undefined>();
  const submitting = useRef(false),
    executionKey = useRef<{ id: string; key: string } | null>(null),
    confirmedIntent = useRef<string | null>(null);
  const [accountsOpen, setAccountsOpen] = useState(
    () => !window.matchMedia("(max-width:650px)").matches,
  );
  useEffect(() => {
    const media = window.matchMedia("(max-width:650px)");
    const resize = () => setAccountsOpen(!media.matches);
    media.addEventListener("change", resize);
    return () => media.removeEventListener("change", resize);
  }, []);
  const clearToast = useCallback(() => setToast(""), []);
  const refresh = useCallback(async () => {
    const result = await api("/api/accounts/balance");
    if (result.verdict === "BLOCK") throw new Error(result.reason);
    setBank(result);
    return result;
  }, []);
  useEffect(() => {
    if (user !== "analyst") refresh().catch((e: Error) => setError(e.message));
  }, [refresh, user]);
  async function send(text: string): Promise<boolean> {
    if (submitting.current || user === "analyst") return false;
    submitting.current = true;
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
      setEntries((old) =>
        [...old, { text, result, timestamp: Date.now() }].slice(-20),
      );
      if (result.intent_id) {
        setProposal(result);
        executionKey.current = null;
        confirmedIntent.current = null;
      }
      try {
        await refresh();
      } catch (e) {
        setError((e as Error).message);
      }
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  async function confirm(cancel = false) {
    if (
      submitting.current ||
      !proposal?.transaction ||
      !proposal.intent_id ||
      user === "analyst"
    )
      return;
    if (
      !["PENDING_CONFIRMATION", "CONFIRMED"].includes(
        proposal.transaction.status,
      ) ||
      proposal.transaction.expires_at * 1000 <= Date.now()
    )
      return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setReceiptBalance(undefined);
    setPreviousBalance(
      bank?.accounts.find(
        (account) => account.name === proposal.transaction?.source_account,
      )?.balance_minor,
    );
    const id = proposal.intent_id;
    try {
      let result = proposal;
      if (
        (confirmedIntent.current !== id &&
          proposal.transaction.status !== "CONFIRMED") ||
        cancel
      ) {
        result = await api(`/api/intents/${id}/confirm`, {
          integrity_tag: proposal.transaction.integrity_tag,
          action: cancel ? "cancel" : "confirm",
        });
        setProposal(result);
        if (result.approved && !cancel) confirmedIntent.current = id;
      }
      if (
        !cancel &&
        (result.approved ||
          confirmedIntent.current === id ||
          proposal.transaction.status === "CONFIRMED")
      ) {
        if (executionKey.current?.id !== id)
          executionKey.current = { id, key: crypto.randomUUID() };
        result = await api("/api/transfers/execute", {
          intent_id: id,
          idempotency_key: executionKey.current.key,
        });
        setProposal(result);
        if (result.transaction?.status === "EXECUTED")
          setToast("Payment completed. Your balance is updated.");
      }
      if (cancel && result.transaction?.status === "CANCELLED")
        setToast("Payment cancelled. No money moved.");
      if (result.verdict === "BLOCK") setError(result.reason);
      const updated = await refresh();
      if (result.transaction?.status === "EXECUTED")
        setReceiptBalance(
          updated.accounts.find(
            (account) => account.name === result.transaction?.source_account,
          )?.balance_minor,
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  if (user === "analyst")
    return (
      <Card>
        <EmptyState
          title="Customer banking workspace"
          description="Switch to Aditi or Rahul to use their synthetic accounts. Analyst identities cannot authorize payments."
        />
      </Card>
    );
  const payee = user === "alice" ? "Rahul" : "Aditi";
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SAFE BANKING, STEP BY STEP</div>
          <h1>Your intent. Under your control.</h1>
          <p>
            Ask a question, review the details, and authorize only what you
            intend.
          </p>
        </div>
        <Badge tone="allow">
          <ShieldCheck size={14} aria-hidden="true" /> Execution guard active
        </Badge>
      </div>
      {error && (
        <ErrorState
          message={error}
          action={
            <button
              className="btn"
              disabled={busy}
              onClick={() =>
                void refresh()
                  .then(() => setError(""))
                  .catch((e: Error) => setError(e.message))
              }
            >
              Refresh accounts
            </button>
          }
        />
      )}
      <div className="bank-layout">
        <div className="chat-column">
          <BankingChat
            user={user}
            entries={entries}
            busy={busy}
            onSend={send}
            review={
              <TransactionReview
                proposal={proposal}
                busy={busy}
                onConfirm={() => void confirm()}
                onCancel={() => void confirm(true)}
                newBalance={receiptBalance}
                previousBalance={previousBalance}
              />
            }
          />
        </div>
        <aside className="account-rail">
          <details
            className="account-disclosure"
            open={accountsOpen}
            onToggle={(event) => setAccountsOpen(event.currentTarget.open)}
          >
            <summary>
              <Wallet size={19} aria-hidden="true" />
              Your accounts
              <ChevronDown size={16} aria-hidden="true" />
            </summary>
            <div className="account-content">
              {bank ? (
                bank.accounts.map((a) => (
                  <Card className="account-card" key={a.id}>
                    <div className="account-card-top">
                      <span>{humanize(a.name)}</span>
                      <span className="mono caption">
                        {maskAccount(a.masked_account)}
                      </span>
                    </div>
                    <strong>{money(a.balance_minor, a.currency)}</strong>
                    <span className="muted caption">
                      Synthetic available balance
                    </span>
                  </Card>
                ))
              ) : error ? (
                <EmptyState
                  title="Accounts unavailable"
                  description="Use Refresh accounts above to try again."
                />
              ) : (
                <>
                  <Skeleton className="account-skeleton" />
                  <Skeleton className="account-skeleton" />
                </>
              )}
              <Card className="payees">
                <h3>Try a demo payee</h3>
                <p className="small muted">
                  Sentinel checks registration and approval when you prepare.
                </p>
                <button
                  className="payee-chip"
                  disabled={busy}
                  onClick={() => void send(`Transfer ₹800 to ${payee}`)}
                >
                  <span className="payee-avatar">{payee[0]}</span>
                  {payee}
                  <ArrowUpRight size={15} aria-hidden="true" />
                </button>
              </Card>
            </div>
          </details>
          <Card className="activity">
            <div className="panel-heading">
              <h2>Recent activity</h2>
              <span className="caption muted">LAST 5</span>
            </div>
            {bank?.history.length ? (
              bank.history.map((t) => (
                <div className="activity-row" key={t.id}>
                  <span className="activity-icon">
                    <ArrowUpRight size={16} aria-hidden="true" />
                  </span>
                  <div>
                    <strong>To {t.beneficiary_name}</strong>
                    <small>{shortTime(t.timestamp)}</small>
                  </div>
                  <span className="amount">
                    −{money(t.amount_minor, t.currency)}
                  </span>
                </div>
              ))
            ) : (
              <EmptyState
                title="No transfers yet"
                description="Your completed payments will appear here."
              />
            )}
          </Card>
          <div className="guard-note">
            <LockKeyhole size={19} aria-hidden="true" />
            <div>
              <strong>Detection is one layer.</strong>
              <p>
                The independent guard checks consent, integrity, expiry, policy
                and replay protection before every payment.
              </p>
            </div>
          </div>
        </aside>
      </div>
      <Toast message={toast} onClose={clearToast} />
    </>
  );
}
