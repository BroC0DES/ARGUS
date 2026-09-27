# mock-codebase2 — live-executing demo services

Unlike `sample_repo` (indexed as static text only), every service here is a real,
separately-running HTTP server that genuinely executes its business logic and
genuinely calls its real dependencies over the network — so editing a file and
saving it actually changes what happens, live.

## Run it

```
cd mock-codebase2
npm install
node dev.mjs               # starts all 6 services + the mock external gateway,
                            # each under `tsx watch` (auto-restarts on file save)
node traffic_sim2.mjs       # separate terminal: fires real checkout requests at
                            # api-gateway on an interval -- whatever genuinely
                            # happens (success, a real timeout, a real pool
                            # exhaustion) gets logged as it occurs
```

Point the backend at this codebase in `backend/.env`:
```
REPO_PATH=<path-to>/mock-codebase2/packages
```
`ARGUS_LOG_PATH` (read by every service via `shared/logger.ts`) defaults to
`../backend/logs/app.log` relative to this folder; override it if your layout
differs.

## The two bugs

- **BUG #1** — `packages/payment-service/src/gateway.ts`: `timeoutMs`. `3000` (as
  shipped) fires too eagerly against the mock gateway's real, randomized latency;
  `8000` gives it headroom. Editing this and saving restarts payment-service
  within a couple seconds (its own `tsx watch` process only).
- **BUG #2** — `packages/db-pool/src/pool.ts`: `maxConnections`. `5` (as shipped)
  or lower gets exhausted under real concurrent load from payment-service,
  orders-service, and ledger-worker (all genuinely share this one process's
  connection count, over real HTTP); `50` gives headroom. notify-worker has no
  dependency on db-pool and stays healthy regardless.

Both bug files' actual logic (the constant and the surrounding decision code) are
completely unmodified from the original spec. Two necessary changes were made
elsewhere so live traffic could genuinely exercise them, both clearly commented
at the change site:
- `gateway.ts`'s fetch target was repointed from a nonexistent domain
  (`mock-gateway.internal`) to `mock-gateway/server.ts`, a real local server with
  randomized latency straddling 3000ms/8000ms -- the original URL never resolved,
  so the timeout would never have depended on the constant's value at all.
- `pool.ts`'s `withConnection()` gained a small artificial delay representing how
  long a real DB call actually holds a connection. Without it, `active` can
  structurally never exceed 1 under any real traffic pattern -- Node's event loop
  fully drains one request's microtask chain (including the decrement) before it
  starts handling the next separate incoming HTTP connection, so `maxConnections`
  could never be genuinely exhausted by real concurrent load, no matter how much
  of it there was.

## Why some service files aren't what's actually running

Each service's original file (`checkout.ts`, `charge.ts`, `router.ts`, `ledger.ts`,
etc.) is untouched and still on disk -- it's still what the Code Indexer parses for
the dependency graph and for retrieval/citations. The actual live wiring is each
service's new `server.ts`, which makes real HTTP calls to the other now-separately-
running services rather than the original direct in-process imports (necessary so
things like db-pool's connection count are genuinely shared across processes,
which a direct import across separate `tsx watch` processes cannot give you).
`orders-service -> ledger-worker` is a new edge that didn't exist in the original
call graph at all (nothing called ledger-worker before); it's imported unused in
`orders-service/src/server.ts` purely so the Code Indexer still detects it
statically.

## traffic_sim2.mjs

Fires `TRAFFIC_BURST_SIZE` (default 4) genuinely concurrent checkout requests
every `TRAFFIC_INTERVAL_MS` (default 800) -- concurrency matters for BUG #2, since
a connection pool can only be exhausted by requests that actually overlap.
