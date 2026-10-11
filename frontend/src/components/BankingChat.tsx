import { useState } from "react";
import type { Result } from "../services/api";
export interface ChatEntry {
  text: string;
  result: Result;
}
export default function BankingChat({
  entries,
  busy,
  onSend,
}: {
  entries: ChatEntry[];
  busy: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");
  function send(value: string) {
    if (!value.trim() || busy) return;
    onSend(value);
    setText("");
  }
  return (
    <section className="panel chat-panel">
      <div className="panel-heading">
        <h2>Banking assistant</h2>
        <span className="pill">GUARDED SESSION</span>
      </div>
      <div className="chat-messages">
        {entries.length === 0 ? (
          <div className="chat-intro">
            <div className="shield">◇</div>
            <h3>Your intent. Safely understood.</h3>
            <p className="muted">
              Check your balance, review activity, or prepare a transfer.
              <br />
              Every payment requires your explicit confirmation.
            </p>
            <div className="quick-actions">
              {[
                "Show my account balance",
                "Show my last five transactions",
                "Transfer ₹1,500 to Rahul",
              ].map((t) => (
                <button key={t} onClick={() => send(t)} disabled={busy}>
                  {t}
                  <span>↗</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          entries.map((entry, i) => (
            <div className="chat-turn" key={i}>
              <div className="user-bubble">{entry.text}</div>
              <div className="assistant-bubble">
                <span className={"badge " + entry.result.verdict.toLowerCase()}>
                  {entry.result.verdict}
                </span>
                <p>{entry.result.reason}</p>
              </div>
            </div>
          ))
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(text);
        }}
      >
        <label className="sr-only" htmlFor="message">
          Banking request
        </label>
        <div className="input-wrap">
          <textarea
            id="message"
            maxLength={2000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask a banking question or prepare a transfer…"
            rows={2}
            disabled={busy}
          />
          <button
            className="send-button"
            type="submit"
            disabled={busy || !text.trim()}
            aria-label="Send request"
          >
            {busy ? "…" : "↑"}
          </button>
        </div>
        <div className="composer-footer">
          <span>Protected by Financial Intent Lock</span>
          <span>{text.length}/2000</span>
        </div>
      </form>
    </section>
  );
}
