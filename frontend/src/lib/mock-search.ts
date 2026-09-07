import { MOCK_CATALOGUE } from "@/lib/mock-catalogue";
import type { SearchResponse } from "@/types/product";

/**
 * Stands in for `GET /search` until the FastAPI backend exists (Stage 5). This is a UI
 * scaffolding aid, not a documented retrieval experiment — the real substring/token baselines
 * (EXP1, EXP2) are measured against the real catalogue in Stage 3 and recorded in
 * experiments/experiment_register.md. This function exists only so every page state (loading,
 * empty, error, success) can be demonstrated in the browser before there is a backend.
 *
 * Two debug-only query prefixes let the UI states be demonstrated on demand:
 *   "simulate:error" -> always rejects, to preview the error state
 *   "simulate:empty" -> always resolves with zero results, to preview the empty state
 */
export function searchProductsMock(query: string): Promise<SearchResponse> {
  const trimmed = query.trim();
  const searchRequestId = `srch_mock_${Math.random().toString(36).slice(2, 10)}`;

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (trimmed.toLowerCase() === "simulate:error") {
        reject(new Error("Simulated search failure (debug query)."));
        return;
      }

      const results =
        trimmed.toLowerCase() === "simulate:empty" || trimmed === ""
          ? []
          : MOCK_CATALOGUE.filter((product) => {
              const haystack =
                `${product.title} ${product.brand} ${product.category} ${product.colour}`.toLowerCase();
              return trimmed
                .toLowerCase()
                .split(/\s+/)
                .filter(Boolean)
                .every((term) => haystack.includes(term));
            });

      resolve({
        searchRequestId,
        query: trimmed,
        interpretation: null,
        modelVersion: "static_mock_v0",
        fallbackUsed: false,
        results,
      });
    }, 400);
  });
}
