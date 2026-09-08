import Link from "next/link";

import type { Product } from "@/types/product";

export function ProductCard({ product, onClick }: { product: Product; onClick?: () => void }) {
  return (
    <li className="group flex flex-col overflow-hidden rounded-lg border border-neutral-200 bg-white transition-shadow hover:shadow-md">
      <Link
        href={`/products/${encodeURIComponent(product.productId)}`}
        onClick={onClick}
        className="flex flex-col focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900"
      >
        <div className="relative">
          <div
            role="img"
            aria-label={product.imageAlt}
            className="flex aspect-[3/4] items-center justify-center bg-neutral-100 text-sm text-neutral-400 transition-colors group-hover:bg-neutral-200/70"
          >
            Image placeholder
          </div>
          {!product.inStock && (
            <span className="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-xs font-medium text-neutral-600 shadow-sm">
              Out of stock
            </span>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-1 p-3">
          {product.brand && (
            <p className="text-xs uppercase tracking-wide text-neutral-500">{product.brand}</p>
          )}
          <h3 className="text-sm font-medium text-neutral-900 group-hover:underline">
            {product.title}
          </h3>
          <p className="text-sm text-neutral-600">{product.colour}</p>
          <p className="mt-0.5 text-sm font-semibold text-neutral-900">£{product.price.toFixed(2)}</p>
        </div>
      </Link>
    </li>
  );
}
