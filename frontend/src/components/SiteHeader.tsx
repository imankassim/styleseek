"use client";

import Link from "next/link";

import { useBasket } from "@/lib/basket-context";

export function SiteHeader() {
  const { totalItems } = useBasket();

  return (
    <header className="border-b border-neutral-200">
      <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold text-neutral-900">
          StyleSeek
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link href="/browse" className="text-neutral-700 hover:text-neutral-900">
            Browse
          </Link>
          <Link href="/basket" className="text-neutral-700 hover:text-neutral-900">
            Basket{totalItems > 0 && ` (${totalItems})`}
          </Link>
        </div>
      </nav>
    </header>
  );
}
