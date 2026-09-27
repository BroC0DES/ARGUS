#!/usr/bin/env node
// Spawns every live service as its OWN process (so a crash or a hot-reload in one
// never touches the others -- required for the syntax-error test in PROMPT 2 #4d/e),
// each running `tsx watch`, so editing any .ts file it depends on restarts just
// that one process within a couple seconds. Run with: node dev.mjs
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOG_PATH = process.env.ARGUS_LOG_PATH || path.resolve(__dirname, "../backend/logs/app.log");
const env = { ...process.env, ARGUS_LOG_PATH: LOG_PATH };

const tsx = path.join(__dirname, "node_modules", ".bin", process.platform === "win32" ? "tsx.cmd" : "tsx");

const services = [
  { name: "mock-gateway", cwd: __dirname, args: ["watch", "mock-gateway/server.ts"] },
  { name: "db-pool", cwd: path.join(__dirname, "packages/db-pool"), args: ["watch", "src/server.ts"] },
  { name: "payment-service", cwd: path.join(__dirname, "packages/payment-service"), args: ["watch", "src/server.ts"] },
  { name: "ledger-worker", cwd: path.join(__dirname, "packages/ledger-worker"), args: ["watch", "src/server.ts"] },
  { name: "notify-worker", cwd: path.join(__dirname, "packages/notify-worker"), args: ["watch", "src/server.ts"] },
  { name: "orders-service", cwd: path.join(__dirname, "packages/orders-service"), args: ["watch", "src/server.ts"] },
  { name: "api-gateway", cwd: path.join(__dirname, "packages/api-gateway"), args: ["watch", "src/server.ts"] },
];

console.log(`[dev] starting ${services.length} services, logging to ${LOG_PATH}`);

for (const svc of services) {
  const child = spawn(tsx, svc.args, { cwd: svc.cwd, env, shell: true });
  const prefix = `[${svc.name}]`;
  child.stdout.on("data", (d) => process.stdout.write(`${prefix} ${d}`));
  child.stderr.on("data", (d) => process.stderr.write(`${prefix} ${d}`));
  child.on("exit", (code) => {
    process.stderr.write(`${prefix} process exited (code ${code}) -- other services keep running\n`);
  });
}
