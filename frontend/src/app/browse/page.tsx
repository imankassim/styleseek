"use client";

import { useEffect, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { listCategories, listProducts, type ListProductsParams } from "@/lib/products-api";
import type { CategorySummary, Product } from "@/types/product";

const PAGE_SIZE = 24;

type ListState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; results: Product[]; total: number };

export default function BrowsePage() {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [category, setCategory] = useState<string>("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [sort, setSort] = useState<ListProductsParams["sort"]>("relevance");
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  function resetToFirstPage() {
    setOffset(0);
  }

  const params: ListProductsParams = {
    category: category || undefined,
    minPrice: minPrice ? Number(minPrice) : undefined,
    maxPrice: maxPrice ? Number(maxPrice) : undefined,
    inStockOnly: inStockOnly || undefined,
    sort,
    limit: PAGE_SIZE,
    offset,
  };
  const queryKey = JSON.stringify(params);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight text-neutral-900">Browse</h1>

      <div className="flex flex-wrap items-end gap-5 rounded-lg border border-neutral-200 bg-neutral-50 p-4">
        <div>
          <label htmlFor="category" className="mb-1 block text-xs font-medium text-neutral-700">
            Category
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              resetToFirstPage();
            }}
            className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.category} value={c.category}>
                {c.category} ({c.productCount})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="minPrice" className="mb-1 block text-xs font-medium text-neutral-700">
            Min price
          </label>
          <input
            id="minPrice"
            type="number"
            min={0}
            value={minPrice}
            onChange={(e) => {
              setMinPrice(e.target.value);
              resetToFirstPage();
            }}
            className="w-24 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
          />
        </div>

        <div>
          <label htmlFor="maxPrice" className="mb-1 block text-xs font-medium text-neutral-700">
            Max price
          </label>
          <input
            id="maxPrice"
            type="number"
            min={0}
            value={maxPrice}
            onChange={(e) => {
              setMaxPrice(e.target.value);
              resetToFirstPage();
            }}
            className="w-24 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
          />
        </div>

        <div>
          <label htmlFor="sort" className="mb-1 block text-xs font-medium text-neutral-700">
            Sort
          </label>
          <select
            id="sort"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value as ListProductsParams["sort"]);
              resetToFirstPage();
            }}
            className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            <option value="relevance">Default</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
          </select>
        </div>

        <label className="flex items-center gap-2 pb-1.5 text-sm text-neutral-700">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(e) => {
              setInStockOnly(e.target.checked);
              resetToFirstPage();
            }}
            className="h-4 w-4 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
          />
          In stock only
        </label>
      </div>

      {/* Keyed on the full query so each distinct filter/page combination gets a fresh
          "loading" state on mount, rather than needing a synchronous reset inside an effect. */}
      <BrowseResults key={queryKey} params={params} offset={offset} onOffsetChange={setOffset} />
    </main>
  );
}

function BrowseResults({
  params,
  offset,
  onOffsetChange,
}: {
  params: ListProductsParams;
  offset: number;
  onOffsetChange: (offset: number) => void;
}) {
  const [state, setState] = useState<ListState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    listProducts(params)
      .then((response) => {
        if (cancelled) return;
        setState({ status: "success", results: response.results, total: response.total });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Unknown error.",
        });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- params is already the effect's identity via the parent's `key`
  }, []);

  if (state.status === "loading") {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (state.status === "error") {
    return (
      <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4">
        <p className="font-medium text-red-800">Something went wrong.</p>
        <p className="mt-1 text-sm text-red-700">{state.message}</p>
      </div>
    );
  }

  if (state.results.length === 0) {
    return <p className="text-neutral-600">No products match these filters.</p>;
  }

  return (
    <>
      <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {state.results.map((product) => (
          <ProductCard key={product.productId} product={product} />
        ))}
      </ul>

      <div className="flex items-center justify-between border-t border-neutral-200 pt-4 text-sm text-neutral-600">
        <span>
          {offset + 1}–{Math.min(offset + PAGE_SIZE, state.total)} of {state.total}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={offset === 0}
            onClick={() => onOffsetChange(Math.max(0, offset - PAGE_SIZE))}
            className="rounded-md border border-neutral-300 px-3 py-1.5 font-medium text-neutral-700 transition-colors hover:border-neutral-900 hover:text-neutral-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-neutral-300 disabled:hover:text-neutral-700"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={offset + PAGE_SIZE >= state.total}
            onClick={() => onOffsetChange(offset + PAGE_SIZE)}
            className="rounded-md border border-neutral-300 px-3 py-1.5 font-medium text-neutral-700 transition-colors hover:border-neutral-900 hover:text-neutral-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-neutral-300 disabled:hover:text-neutral-700"
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}
