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

  const exampleQueries = ["black nike shoes", "red dress under £50", "smart casual blazer"];

  function runExample(example: string) {
    setQuery(example);
    runSearch(example);
  }

  return (
    <main className="flex flex-1 flex-col">
      <section className="border-b border-neutral-200 bg-neutral-50">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-6 px-6 py-16 text-center">
          <h1 className="text-4xl font-semibold tracking-tight text-neutral-900 sm:text-5xl">
            Find your style
          </h1>
          <p className="max-w-md text-neutral-600">
            An original fashion search prototype — hybrid lexical and semantic search, described
            fully in the write-up below.
          </p>

          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={runSearch}
            isLoading={state.status === "loading"}
          />

          {state.status === "idle" && (
            <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
              <span className="text-neutral-500">Try:</span>
              {exampleQueries.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => runExample(example)}
                  className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-neutral-700 transition-colors hover:border-neutral-900 hover:text-neutral-900"
                >
                  {example}
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center px-6 py-12">
        <ResultsGrid state={state} onRetry={() => runSearch(query)} />
      </div>
    </main>
  );
}
