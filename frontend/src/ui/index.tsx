import {
  useEffect,
  useId,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  LoaderCircle,
  ShieldCheck,
  X,
} from "lucide-react";
import { formatMoney } from "./format";

export function AnimatedMoney({
  value,
  from,
  currency = "INR",
}: {
  value: number;
  from?: number;
  currency?: string;
}) {
  const [display, setDisplay] = useState(value);
  useEffect(() => {
    if (
      from === undefined ||
      !Number.isSafeInteger(from) ||
      !Number.isSafeInteger(value) ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      setDisplay(value);
      return;
    }
    const start = BigInt(from),
      target = BigInt(value);
    let frame = 0;
    const began = performance.now();
    const tick = (time: number) => {
      const step = Math.min(24, Math.floor((time - began) / 15));
      setDisplay(Number(start + ((target - start) * BigInt(step)) / 24n));
      if (step < 24) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, from]);
  return (
    <span aria-label={formatMoney(value, currency)}>
      <span aria-hidden="true">{formatMoney(display, currency)}</span>
    </span>
  );
}

export function Spinner() {
  return <LoaderCircle className="spinner icon" aria-hidden="true" />;
}
export function Button({
  variant = "secondary",
  loading = false,
  children,
  className = "",
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  loading?: boolean;
}) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`btn btn-${variant} ${className}`}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}
export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`input ${props.className || ""}`} />;
}
export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`input ${props.className || ""}`} />;
}
export function Badge({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone.toLowerCase()}`}>{children}</span>;
}
export function Card({
  children,
  className = "",
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <section {...props} className={`panel ${className}`}>
      {children}
    </section>
  );
}
export function Tooltip({
  text,
  children,
}: {
  text: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <span className="tooltip" tabIndex={0} aria-describedby={id}>
      {children}
      <span className="tooltip-content" role="tooltip" id={id}>
        {text}
      </span>
    </span>
  );
}
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <ShieldCheck aria-hidden="true" />
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}
export function Stat({
  label,
  value,
  note,
  tone = "",
}: {
  label: string;
  value: ReactNode;
  note?: string;
  tone?: string;
}) {
  return (
    <Card className={`stat ${tone}`}>
      <span className="muted small">{label}</span>
      <strong>{value}</strong>
      {note && <span className="muted caption">{note}</span>}
    </Card>
  );
}
export function KeyValue({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="key-values">
      {rows.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
export function Stepper({
  active,
  terminal,
}: {
  active: number;
  terminal?: string;
}) {
  return (
    <ol className="stepper" aria-label="Payment progress">
      {["Request", "Review", "Confirm", "Executed"].map((step, i) => (
        <li
          key={step}
          className={i <= active ? "complete" : ""}
          aria-current={i === active ? "step" : undefined}
        >
          <span>
            {i < active ? <Check size={12} aria-hidden="true" /> : i + 1}
          </span>
          {terminal && i === active ? terminal : step}
        </li>
      ))}
    </ol>
  );
}
export function Tabs({
  items,
  value,
  onChange,
}: {
  items: { id: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  return (
    <div role="tablist" className="tabs">
      {items.map((item, i) => (
        <button
          key={item.id}
          ref={(node) => {
            refs.current[i] = node;
          }}
          role="tab"
          aria-selected={value === item.id}
          tabIndex={value === item.id ? 0 : -1}
          onClick={() => onChange(item.id)}
          onKeyDown={(event) => {
            let target = i;
            if (event.key === "ArrowRight") target = (i + 1) % items.length;
            else if (event.key === "ArrowLeft")
              target = (i + items.length - 1) % items.length;
            else if (event.key === "Home") target = 0;
            else if (event.key === "End") target = items.length - 1;
            else return;
            event.preventDefault();
            onChange(items[target].id);
            refs.current[target]?.focus();
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
export function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (open) dialog?.showModal();
    else dialog?.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={id}
      onCancel={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="panel-heading">
        <h2 id={id}>{title}</h2>
        <Button variant="ghost" aria-label="Close dialog" onClick={onClose}>
          <X size={20} />
        </Button>
      </div>
      {children}
    </dialog>
  );
}
export function Toast({
  message,
  onClose,
}: {
  message: string;
  onClose: () => void;
}) {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(onClose, 4500);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);
  return message ? (
    <div className="toast" role="status">
      <CheckCircle2 size={18} aria-hidden="true" />
      {message}
      <Button
        variant="ghost"
        aria-label="Dismiss notification"
        onClick={onClose}
      >
        <X size={16} />
      </Button>
    </div>
  ) : null;
}
export function ErrorState({
  message,
  action,
}: {
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="error" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <div>
        <strong>We couldn’t complete that step</strong>
        <p>{message}</p>
        {action}
      </div>
    </div>
  );
}
function withoutSecrets(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(withoutSecrets);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value)
        .filter(
          ([key]) =>
            !/(token|secret|integrity_tag|password|authorization|hmac)/i.test(
              key,
            ),
        )
        .map(([key, item]) => [key, withoutSecrets(item)]),
    );
  return value;
}
export function CodeBlock({ value }: { value: unknown }) {
  const [copied, setCopied] = useState(false),
    [error, setError] = useState("");
  const json = JSON.stringify(withoutSecrets(value), null, 2);
  return (
    <div className="code-block">
      <div>
        <span>JSON · sensitive fields omitted</span>
        <Button
          variant="ghost"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(json);
              setCopied(true);
              setError("");
            } catch {
              setError("Copy unavailable. Select the JSON text manually.");
            }
          }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}{" "}
          {copied ? "Copied" : "Copy JSON"}
        </Button>
      </div>
      <pre tabIndex={0}>{json}</pre>
      {error && <p role="status">{error}</p>}
    </div>
  );
}
export function Table({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label={label}>
      <table>{children}</table>
    </div>
  );
}
