import type { Product } from "@/types/product";

export function ProductCard({ product }: { product: Product }) {
  return (
    <li className="flex flex-col overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-sm">
      <div
        role="img"
        aria-label={product.imageAlt}
        className="flex aspect-[3/4] items-center justify-center bg-neutral-100 text-sm text-neutral-400"
      >
        Image placeholder
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        {product.brand && (
          <p className="text-xs uppercase tracking-wide text-neutral-500">{product.brand}</p>
        )}
        <h3 className="text-sm font-medium text-neutral-900">{product.title}</h3>
        <p className="text-sm text-neutral-700">
          £{product.price.toFixed(2)} · {product.colour}
        </p>
        {!product.inStock && (
          <p className="text-xs font-medium text-red-700">Out of stock</p>
        )}
      </div>
    </li>
  );
}
