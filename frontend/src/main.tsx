import React, { lazy, Suspense, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { configured, login, wake } from "./services/api";
import "./styles.css";
const BankSimulator = lazy(() => import("./pages/BankSimulator"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const AttackLab = lazy(() => import("./pages/AttackLab"));
type Page = "bank" | "dashboard" | "lab";
function App() {
  const [page, setPage] = useState<Page>("bank");
  const [user, setUser] = useState("alice");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setReady(false);
    setError("");
    wake()
      .then(() => login(user))
      .then(() => {
        if (active) setReady(true);
      })
      .catch((e) => {
        if (active) setError(String(e.message));
      });
    return () => {
      active = false;
    };
  }, [user, retry]);
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setPage("bank")}>
          <span className="brand-icon">S</span>
          <span>
            bankism<span className="brand-sub">SENTINEL</span>
          </span>
        </a>
        <div className="workspace-label">SECURE WORKSPACE</div>
        <nav aria-label="Main navigation">
          {(
            [
              ["bank", "◈", "Bank simulator"],
              ["dashboard", "▦", "Security dashboard"],
              ["lab", "⌘", "Attack lab"],
            ] as const
          ).map(([id, icon, label]) => (
            <button
              className={page === id ? "nav-item active" : "nav-item"}
              key={id}
              onClick={() => setPage(id)}
              aria-current={page === id ? "page" : undefined}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" />
          Independent execution guard
          <div className="muted">Every transfer. Every time.</div>
        </div>
      </aside>
      <div className="main-area">
        <header>
          <div className="breadcrumb">
            WORKSPACE <span>/</span>{" "}
            {page === "bank"
              ? "Bank simulator"
              : page === "lab"
                ? "Attack lab"
                : "Security dashboard"}
          </div>
          <label className="session">
            Demo session
            <select value={user} onChange={(e) => setUser(e.target.value)}>
              <option value="alice">Aditi · customer</option>
              <option value="rahul">Rahul · customer</option>
              <option value="analyst">Security analyst</option>
            </select>
          </label>
        </header>
        <div className="demo-banner">
          <span>◉</span> Synthetic demo · No real money or customer data{" "}
          <span className="banner-end">FINANCIAL AI FIREWALL</span>
        </div>
        <main>
          {!configured() ? (
            <div className="panel error">
              API connection is missing. Set VITE_API_BASE_URL to your backend
              address and rebuild.
            </div>
          ) : error ? (
            <div className="panel error" role="alert">
              {error}
              <button onClick={() => setRetry(retry + 1)}>
                Retry connection
              </button>
            </div>
          ) : !ready ? (
            <div className="panel loading" role="status">
              Waking up the secure server…
              <p className="muted">Free hosting can take a moment to start.</p>
            </div>
          ) : (
            <Suspense
              fallback={<div className="panel loading">Loading workspace…</div>}
            >
              {page === "bank" ? (
                <BankSimulator key={user} />
              ) : page === "dashboard" ? (
                <Dashboard key={user} analyst={user === "analyst"} />
              ) : (
                <AttackLab key={user} user={user} />
              )}
            </Suspense>
          )}
        </main>
        <footer>
          Bankism Sentinel{" "}
          <span>AI provides evidence. The guard provides authorization.</span>
          <span>v1.0 · Synthetic banking environment</span>
        </footer>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
