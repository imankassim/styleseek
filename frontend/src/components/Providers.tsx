"use client";

import { BasketProvider } from "@/lib/basket-context";
import { SiteHeader } from "@/components/SiteHeader";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <BasketProvider>
      <SiteHeader />
      {children}
    </BasketProvider>
  );
}
