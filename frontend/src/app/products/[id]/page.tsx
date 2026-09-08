"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { getProduct, getSimilarProducts } from "@/lib/products-api";
import { useBasket } from "@/lib/basket-context";
import { ProductCard } from "@/components/ProductCard";
import type { Product, ProductDetail } from "@/types/product";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "not_found" }
  | { status: "success"; product: ProductDetail };

export default function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  // Keying on id gives each product a fresh component instance — state naturally starts at
  // "loading" again on navigation instead of needing a synchronous reset inside the effect.
  return <ProductDetailView key={id} id={id} />;
}

function ProductDetailView({ id }: { id: string }) {
  const [state, setState] = useState<State>({ status: "loading" });
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [justAdded, setJustAdded] = useState(false);
  // Similar products are a separate, optional, best-effort section (architecture §12 journey
  // 16) — an empty array is the honest default for "not available yet" as well as "genuinely
  // fetched, nothing found" and "the request failed"; none of those should affect the rest of
  // the page.
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const { addItem } = useBasket();

  useEffect(() => {
    let cancelled = false;

    getProduct(id)
      .then((product) => {
        if (cancelled) return;
        setState({ status: "success", product });
        setSelectedSize(product.variants.find((v) => v.stockQuantity > 0)?.size ?? null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof Error && error.message.includes("(404)")) {
          setState({ status: "not_found" });
        } else {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : "Unknown error.",
          });
        }
      });

    getSimilarProducts(id)
      .then((products) => {
        if (!cancelled) setSimilarProducts(products);
      })
      .catch(() => {
        // Best-effort — a failed similar-products lookup shouldn't affect the main product view.
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (state.status === "loading") {
    return <main className="mx-auto max-w-3xl px-6 py-12 text-neutral-600">Loading…</main>;
  }

  if (state.status === "not_found") {
    return (
      <main className="mx-auto max-w-3xl px-6 py-12">
        <p className="font-medium text-neutral-900">Product not found.</p>
        <Link href="/browse" className="mt-2 inline-block text-sm underline">
          Back to browse
        </Link>
      </main>
    );
  }

  if (state.status === "error") {
    return (
      <main className="mx-auto max-w-3xl px-6 py-12">
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">Something went wrong.</p>
          <p className="mt-1 text-sm text-red-700">{state.message}</p>
        </div>
      </main>
    );
  }

  const { product } = state;
  const selectedVariant = product.variants.find((v) => v.size === selectedSize) ?? null;

  function handleAddToBasket() {
    if (!selectedVariant) return;
    addItem({
      variantId: selectedVariant.variantId,
      productId: product.productId,
      title: product.title,
      colour: selectedVariant.colour,
      size: selectedVariant.size,
      price: product.price,
      sku: selectedVariant.sku,
    });
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 2000);
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-12 px-6 py-12">
      <Link
        href="/browse"
        className="-mb-4 flex items-center gap-1 text-sm text-neutral-500 transition-colors hover:text-neutral-900"
      >
        ← Back to browse
      </Link>

      <div className="flex w-full flex-col gap-10 md:flex-row">
        <div
          role="img"
          aria-label={product.imageAlt}
          className="flex aspect-[3/4] w-full items-center justify-center bg-neutral-100 text-sm text-neutral-400 md:w-1/2"
        >
          Image placeholder
        </div>

        <div className="flex flex-1 flex-col gap-3">
          {product.brand && (
            <p className="text-xs uppercase tracking-wide text-neutral-500">{product.brand}</p>
          )}
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">{product.title}</h1>
          <p className="text-xl font-semibold text-neutral-900">£{product.price.toFixed(2)}</p>
          <p className="text-sm text-neutral-600">
            {product.category}
            {product.occasion ? ` · ${product.occasion}` : ""}
          </p>

          <fieldset className="mt-4 border-t border-neutral-200 pt-4">
            <legend className="mb-2 text-sm font-medium text-neutral-900">Size</legend>
            <div className="flex flex-wrap gap-2">
              {product.variants.map((variant) => (
                <button
                  key={variant.variantId}
                  type="button"
                  disabled={variant.stockQuantity === 0}
                  aria-pressed={selectedSize === variant.size}
                  onClick={() => setSelectedSize(variant.size)}
                  className={`rounded-md border px-3 py-1.5 text-sm ${
                    selectedSize === variant.size
                      ? "border-neutral-900 bg-neutral-900 text-white"
                      : "border-neutral-300 bg-white text-neutral-900 hover:border-neutral-500"
                  } disabled:cursor-not-allowed disabled:opacity-40`}
                >
                  {variant.size}
                </button>
              ))}
            </div>
          </fieldset>

          <button
            type="button"
            onClick={handleAddToBasket}
            disabled={!selectedVariant || selectedVariant.stockQuantity === 0}
            className="mt-4 w-fit rounded-md bg-neutral-900 px-5 py-2.5 font-medium text-white hover:bg-neutral-700 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {justAdded ? "Added ✓" : "Add to basket"}
          </button>

          {!selectedVariant && (
            <p className="text-xs text-red-700">This item is currently out of stock.</p>
          )}
        </div>
      </div>

      {similarProducts.length > 0 && (
        <section aria-labelledby="similar-styles-heading">
          <h2 id="similar-styles-heading" className="mb-4 text-lg font-semibold text-neutral-900">
            Similar styles
          </h2>
          <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {similarProducts.map((similar) => (
              <ProductCard key={similar.productId} product={similar} />
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
