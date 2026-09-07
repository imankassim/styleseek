"use client";

import { useCallback, useState } from "react";

import { SearchBar } from "@/components/SearchBar";
import { ResultsGrid, type SearchState } from "@/components/ResultsGrid";
import { searchProducts } from "@/lib/search-api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<SearchState>({ status: "idle" });

  const runSearch = useCallback((submittedQuery: string) => {
    if (submittedQuery.trim() === "") {
      setState({ status: "idle" });
      return;
    }

    setState({ status: "loading" });
    searchProducts(submittedQuery)
      .then((response) => setState({ status: "success", response }))
      .catch((error: unknown) =>
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Unknown error.",
        }),
      );
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center gap-8 px-6 py-12">
      <header className="flex w-full max-w-2xl flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold text-neutral-900">StyleSeek</h1>
        <p className="text-neutral-600">
          An original fashion search prototype — search below to see it in action.
        </p>
      </header>

      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={runSearch}
        isLoading={state.status === "loading"}
      />

      <ResultsGrid state={state} onRetry={() => runSearch(query)} />
    </main>
  );
}
