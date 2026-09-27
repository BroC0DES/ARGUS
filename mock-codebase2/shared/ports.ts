// Fixed local ports for the 6 live services + the mock external payment gateway.
// Every inter-service call in every server.ts uses these, via ARGUS_<NAME>_URL env
// vars when set (so this is still overridable per machine), falling back to
// localhost:<port> for a normal single-machine dev run.
export const PORTS = {
  apiGateway: 4000,
  ordersService: 4001,
  paymentService: 4002,
  dbPool: 4003,
  ledgerWorker: 4004,
  notifyWorker: 4005,
  mockGateway: 4099,
};

function url(envVar: string, port: number): string {
  return process.env[envVar] || `http://localhost:${port}`;
}

export const URLS = {
  apiGateway: url("ARGUS_API_GATEWAY_URL", PORTS.apiGateway),
  ordersService: url("ARGUS_ORDERS_SERVICE_URL", PORTS.ordersService),
  paymentService: url("ARGUS_PAYMENT_SERVICE_URL", PORTS.paymentService),
  dbPool: url("ARGUS_DB_POOL_URL", PORTS.dbPool),
  ledgerWorker: url("ARGUS_LEDGER_WORKER_URL", PORTS.ledgerWorker),
  notifyWorker: url("ARGUS_NOTIFY_WORKER_URL", PORTS.notifyWorker),
  mockGateway: url("ARGUS_MOCK_GATEWAY_URL", PORTS.mockGateway),
};
