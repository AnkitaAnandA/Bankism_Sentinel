import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  FlaskConical,
  Landmark,
  LockKeyhole,
  Moon,
  ShieldCheck,
  Sun,
  Activity,
  ChevronRight,
} from "lucide-react";
import { configured, login, wake } from "./services/api";
import { Button, Card, ErrorState, Skeleton, Spinner, Tooltip } from "./ui";
import "./styles.css";
const BankSimulator = lazy(() => import("./pages/BankSimulator"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const AttackLab = lazy(() => import("./pages/AttackLab"));
type Page = "bank" | "dashboard" | "lab";
const pages = [
  { id: "bank" as const, label: "Bank Simulator", icon: Landmark },
  { id: "dashboard" as const, label: "Security Dashboard", icon: Activity },
  { id: "lab" as const, label: "Attack Lab", icon: FlaskConical },
];
let sessionQueue: Promise<void> = Promise.resolve();
function App() {
  const [page, setPage] = useState<Page>("bank"),
    [user, setUser] = useState("alice"),
    [ready, setReady] = useState(false),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  const [dark, setDark] = useState(
    () => document.documentElement.dataset.theme === "dark",
  );
  const sessionVersion = useRef(0);
  const [backendOnline, setBackendOnline] = useState(false);
  useEffect(() => {
    const update = (event: Event) => {
      if (event instanceof CustomEvent) setBackendOnline(Boolean(event.detail));
    };
    window.addEventListener("sentinel:connection", update);
    return () => window.removeEventListener("sentinel:connection", update);
  }, []);
  useEffect(() => {
    let active = true;
    const version = ++sessionVersion.current;
    setReady(false);
    setError("");
    sessionQueue = sessionQueue
      .catch(() => {})
      .then(async () => {
        if (!active) return;
        await wake();
        if (!active) return;
        await login(user);
        if (active && version === sessionVersion.current) setReady(true);
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [user, retry]);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      let saved = false;
      try {
        saved = Boolean(localStorage.getItem("sentinel-theme"));
      } catch {
        /* system preference still works */
      }
      if (!saved) {
        document.documentElement.dataset.theme = media.matches
          ? "dark"
          : "light";
        setDark(media.matches);
      }
    };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  function switchUser(value: string) {
    setReady(false);
    setUser(value);
    setPage(value === "analyst" ? "dashboard" : "bank");
  }
  function theme() {
    const next = !dark;
    document.documentElement.dataset.theme = next ? "dark" : "light";
    setDark(next);
    try {
      localStorage.setItem("sentinel-theme", next ? "dark" : "light");
    } catch {
      /* preference is optional */
    }
  }
  function navigation(mobile = false) {
    return (
      <nav
        aria-label={mobile ? "Mobile navigation" : "Main navigation"}
        className={mobile ? "mobile-nav" : "desktop-nav"}
      >
        {pages.map(({ id, label, icon: Icon }) => {
          const locked = id === "dashboard" && user !== "analyst";
          const item = (
            <button
              key={id}
              disabled={locked}
              aria-label={locked ? `${label} — analyst access required` : label}
              aria-current={page === id ? "page" : undefined}
              className={`nav-item ${page === id ? "active" : ""}`}
              onClick={() => setPage(id)}
            >
              <Icon size={20} aria-hidden="true" />
              <span>
                {mobile
                  ? id === "bank"
                    ? "Bank"
                    : id === "dashboard"
                      ? "Security"
                      : "Attack Lab"
                  : label}
              </span>
              {locked && <LockKeyhole size={14} aria-hidden="true" />}
            </button>
          );
          return locked ? (
            <Tooltip
              key={id}
              text="Switch to the Analyst demo identity to inspect protected audit records."
            >
              {item}
            </Tooltip>
          ) : (
            item
          );
        })}
      </nav>
    );
  }
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(event) => {
            event.preventDefault();
            setPage(user === "analyst" ? "dashboard" : "bank");
          }}
        >
          <span className="brand-icon">
            <ShieldCheck size={25} aria-hidden="true" />
          </span>
          <span>
            Bankism<span className="brand-sub">SENTINEL</span>
          </span>
        </a>
        <div className="workspace-label">DEMO WORKSPACE</div>
        {navigation()}
        <div className="sidebar-footer">
          <ShieldCheck size={18} aria-hidden="true" />
          <strong>Authorization is independent.</strong>
          <p>Every payment passes the execution guard.</p>
          <span className="caption">SYNTHETIC BANKING · v1.0</span>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={14} aria-hidden="true" />
            <strong>{pages.find((item) => item.id === page)?.label}</strong>
          </div>
          <div className="header-actions">
            <span
              className={`connection ${ready ? (backendOnline ? "connected" : "offline") : error ? "offline" : "waking"}`}
              role="status"
            >
              <i />
              {ready
                ? backendOnline
                  ? "Connected"
                  : "Offline"
                : error
                  ? "Offline"
                  : "Waking up"}
            </span>
            <label className="session">
              <span>Acting as</span>
              <select
                aria-label="Acting as"
                value={user}
                onChange={(event) => switchUser(event.target.value)}
              >
                <option value="alice">Aditi · Customer</option>
                <option value="rahul">Rahul · Customer</option>
                <option value="analyst">Security Analyst</option>
              </select>
            </label>
            <Button
              variant="ghost"
              onClick={theme}
              aria-label={
                dark ? "Switch to light theme" : "Switch to dark theme"
              }
            >
              {dark ? <Sun size={20} /> : <Moon size={20} />}
            </Button>
          </div>
        </header>
        <div className="demo-banner">
          <ShieldCheck size={15} aria-hidden="true" />
          <strong>Demo · synthetic data</strong>
          <span>No real money or real customer data</span>
        </div>
        <main id="main-content" tabIndex={-1}>
          {!configured() ? (
            <ErrorState message="The demo connection isn’t configured. Check the frontend deployment settings." />
          ) : error ? (
            <Card className="connection-card">
              <ErrorState
                message={error}
                action={
                  <Button onClick={() => setRetry(retry + 1)}>
                    Retry connection
                  </Button>
                }
              />
            </Card>
          ) : !ready ? (
            <Card className="connection-card" role="status">
              <Spinner />
              <h1>Waking up the secure server</h1>
              <p>
                Establishing your synthetic demo session. This can take a moment
                on free hosting.
              </p>
              <Skeleton />
              <Skeleton />
            </Card>
          ) : (
            <Suspense
              fallback={
                <Card className="connection-card" role="status">
                  <Spinner />
                  <p>Loading your workspace…</p>
                  <Skeleton />
                </Card>
              }
            >
              {page === "bank" ? (
                <BankSimulator key={user} user={user} />
              ) : page === "dashboard" ? (
                <Dashboard key={user} analyst={user === "analyst"} />
              ) : (
                <AttackLab key={user} user={user} />
              )}
            </Suspense>
          )}
        </main>
        <footer>
          <span>Bankism Sentinel</span>
          <span>AI provides evidence. The guard provides authorization.</span>
          <span>All activity is synthetic.</span>
        </footer>
      </div>
      {navigation(true)}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
