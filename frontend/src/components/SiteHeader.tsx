"use client";

import Link from "next/link";

import { useBasket } from "@/lib/basket-context";

export function SiteHeader() {
  const { totalItems } = useBasket();

  return (
    <header className="sticky top-0 z-10 border-b border-neutral-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link
          href="/"
          className="text-xl font-semibold tracking-tight text-neutral-900"
        >
          StyleSeek
        </Link>
        <div className="flex items-center gap-8 text-sm font-medium">
          <Link href="/browse" className="text-neutral-700 transition-colors hover:text-neutral-900">
            Browse
          </Link>
          <Link
            href="/basket"
            className="flex items-center gap-2 text-neutral-700 transition-colors hover:text-neutral-900"
          >
            Basket
            {totalItems > 0 && (
              <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-neutral-900 px-1.5 text-xs font-semibold text-white">
                {totalItems}
              </span>
            )}
          </Link>
        </div>
      </nav>
    </header>
  );
}
