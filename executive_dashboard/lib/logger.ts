export function logEvent(enabled: boolean, event: string, payload: unknown) {
  if (!enabled) return;
  console.log(`[dashboard:${event}]`, payload);
}
