import { useEffect, useRef } from "react";

import type { SearchResponse } from "@/types/product";
import { ProductCard } from "@/components/ProductCard";
import { recordEvents } from "@/lib/events-api";

export type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; response: SearchResponse };

function InterpretationChips({ interpretation }: { interpretation: SearchResponse["interpretation"] }) {
  if (!interpretation) return null;

  const chips = [
    interpretation.category && `category: ${interpretation.category}`,
    interpretation.colour && `colour: ${interpretation.colour}`,
    interpretation.occasion && `occasion: ${interpretation.occasion}`,
    interpretation.size && `size: ${interpretation.size}`,
    interpretation.maxPrice != null && `under £${interpretation.maxPrice}`,
  ].filter(Boolean) as string[];

  if (chips.length === 0) return null;

  return (
    <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-neutral-600">
      <span>Understood:</span>
      {chips.map((chip) => (
        <span key={chip} className="rounded-full border border-neutral-300 px-2 py-0.5">
          {chip}
        </span>
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <li
      aria-hidden="true"
      className="flex flex-col overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-sm"
    >
      <div className="aspect-[3/4] animate-pulse bg-neutral-100" />
      <div className="flex flex-col gap-2 p-3">
        <div className="h-3 w-1/3 animate-pulse rounded bg-neutral-100" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-neutral-100" />
        <div className="h-3 w-1/4 animate-pulse rounded bg-neutral-100" />
      </div>
    </li>
  );
}

export function ResultsGrid({
  state,
  onRetry,
}: {
  state: SearchState;
  onRetry: () => void;
}) {
  const impressedFor = useRef<string | null>(null);

  useEffect(() => {
    if (state.status !== "success" || state.response.results.length === 0) return;
    if (impressedFor.current === state.response.searchRequestId) return;
    impressedFor.current = state.response.searchRequestId;

    recordEvents(
      state.response.results.map((product, index) => ({
        eventType: "impression",
        searchRequestId: state.response.searchRequestId,
        productId: product.productId,
        position: index,
      })),
    );
  }, [state]);

  return (
    <div aria-live="polite" className="w-full max-w-5xl">
      {state.status === "idle" && (
        <p className="text-neutral-600">
          Search for products above — try &ldquo;black adidas trainers&rdquo; or &ldquo;green
          wedding guest dress&rdquo;.
        </p>
      )}

      {state.status === "loading" && (
        <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))}
        </ul>
      )}

      {state.status === "error" && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">Something went wrong.</p>
          <p className="mt-1 text-sm text-red-700">{state.message}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-800"
          >
            Try again
          </button>
        </div>
      )}

      {state.status === "success" && <InterpretationChips interpretation={state.response.interpretation} />}

      {state.status === "success" && state.response.results.length === 0 && (
        <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4">
          <p className="font-medium text-neutral-900">
            No results for &ldquo;{state.response.query}&rdquo;.
          </p>
          <p className="mt-1 text-sm text-neutral-600">
            Try a broader term, check the spelling, or remove a constraint like size or price.
          </p>
        </div>
      )}

      {state.status === "success" && state.response.results.length > 0 && (
        <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {state.response.results.map((product, index) => (
            <ProductCard
              key={product.productId}
              product={product}
              onClick={() =>
                recordEvents([
                  {
                    eventType: "click",
                    searchRequestId: state.response.searchRequestId,
                    productId: product.productId,
                    position: index,
                  },
                ])
              }
            />
          ))}
        </ul>
      )}
    </div>
  );
}
