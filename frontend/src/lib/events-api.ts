import { apiPost } from "@/lib/api-client";

export type TrackedEvent = {
  eventType: "impression" | "click";
  searchRequestId: string;
  productId: string;
  position: number;
};

/**
 * Fire-and-forget: never blocks or breaks the search UI (architecture §10, "Event collector
 * unavailable: do not block search response"). Failures are swallowed, not surfaced to the
 * shopper — this is instrumentation, not core functionality.
 */
export function recordEvents(events: TrackedEvent[]): void {
  if (events.length === 0) return;

  apiPost("/events", {
    events: events.map((e) => ({
      event_type: e.eventType,
      search_request_id: e.searchRequestId,
      product_id: e.productId,
      position: e.position,
    })),
  }).catch(() => {
    // Instrumentation failure is not the shopper's problem.
  });
}
