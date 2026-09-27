export interface NotifyRequest {
  orderId: string;
  email: string;
}

// notify-worker deliberately has NO dependency on db-pool — it queues
// an email directly. This is intentional: it should stay healthy even
// during the DB-exhaustion scenario, which is a useful contrast in the
// demo ("everything downstream of db-pool fails, but notify-worker,
// which doesn't touch it, keeps working normally").
export async function queueConfirmationEmail(request: NotifyRequest) {
  return { ok: true, orderId: request.orderId, queued: true };
}
