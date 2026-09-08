"use client";

import Link from "next/link";

import { useBasket } from "@/lib/basket-context";

export default function BasketPage() {
  const { items, removeItem, setQuantity, totalPrice } = useBasket();

  if (items.length === 0) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-neutral-900">
          Your basket is empty
        </h1>
        <p className="mb-6 text-neutral-600">Find something you like and add it here.</p>
        <Link
          href="/browse"
          className="inline-block rounded-md bg-neutral-900 px-5 py-2.5 font-medium text-white hover:bg-neutral-700"
        >
          Browse products
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="mb-6 text-3xl font-semibold tracking-tight text-neutral-900">Basket</h1>

      <ul className="flex flex-col gap-4">
        {items.map((item) => (
          <li
            key={item.variantId}
            className="flex items-center justify-between gap-4 rounded-lg border border-neutral-200 bg-white p-4"
          >
            <div>
              <p className="font-medium text-neutral-900">{item.title}</p>
              <p className="text-sm text-neutral-600">
                {item.colour} · Size {item.size} · £{item.price.toFixed(2)}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <label className="sr-only" htmlFor={`qty-${item.variantId}`}>
                Quantity for {item.title}
              </label>
              <input
                id={`qty-${item.variantId}`}
                type="number"
                min={1}
                value={item.quantity}
                onChange={(e) => setQuantity(item.variantId, Number(e.target.value))}
                className="w-16 rounded-md border border-neutral-300 px-2 py-1 text-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
              />
              <button
                type="button"
                onClick={() => removeItem(item.variantId)}
                className="text-sm text-neutral-500 underline underline-offset-2 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-6 flex items-center justify-between border-t border-neutral-200 pt-4">
        <p className="text-lg font-medium text-neutral-900">Total</p>
        <p className="text-lg font-semibold text-neutral-900">£{totalPrice.toFixed(2)}</p>
      </div>
      <p className="mt-2 text-xs text-neutral-500">
        Simulation only — no real payment or order is created (this is a research prototype).
      </p>
    </main>
  );
}
