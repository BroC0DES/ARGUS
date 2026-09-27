// Shared by every service's server.ts wrapper (not a "service" itself -- it lives
// outside packages/, so the Code Indexer's service discovery never counts it as a
// 7th node). Writes real log lines, in the exact format log_analyzer.py's LINE_RE
// expects, to the same LOG_PATH the Python backend reads -- so genuinely live
// traffic through these services shows up in ARGUS exactly like traffic_sim.py's
// output always has.
import * as fs from "fs";
import * as path from "path";

const LOG_PATH =
  process.env.ARGUS_LOG_PATH || path.resolve(__dirname, "../../backend/logs/app.log");

function pad(n: number, width = 2): string {
  return String(n).padStart(width, "0");
}

function stamp(): string {
  const d = new Date();
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(), 3)}`
  );
}

export function log(level: "INFO" | "WARN" | "ERROR", service: string, message: string): void {
  const line = `${stamp()} ${level} ${service} ${message}`;
  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  fs.appendFileSync(LOG_PATH, line + "\n", "utf8");
  // Also visible in this service's own terminal -- required for the syntax-error
  // test (4d): a failure needs to be loud in its own process's output.
  // eslint-disable-next-line no-console
  console.log(line);
}
