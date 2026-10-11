export function formatMoney(minor: number, currency = "INR"): string {
  if (!Number.isSafeInteger(minor)) return "Amount unavailable";
  const n = BigInt(minor);
  const absolute = n < 0n ? -n : n;
  const whole = (absolute / 100n).toLocaleString("en-IN");
  const cents = (absolute % 100n).toString().padStart(2, "0");
  const symbol = currency === "INR" ? "₹" : `${currency} `;
  return `${n < 0n ? "−" : ""}${symbol}${whole}.${cents}`;
}
export function maskAccount(value: string): string {
  const suffix = value.replace(/[•*\s]/g, "").slice(-4);
  return `•••• ${suffix || "—"}`;
}
export const humanize = (value: string) =>
  value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/^./, (c) => c.toUpperCase());
export const shortTime = (seconds: number) =>
  new Date(seconds * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
