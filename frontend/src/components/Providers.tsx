"use client";

import { BasketProvider } from "@/lib/basket-context";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <BasketProvider>
      <SiteHeader />
      {children}
      <SiteFooter />
    </BasketProvider>
  );
}
