"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";

/**
 * Basket simulation only — no real payments or order fulfilment (architecture §2.2). State
 * lives in this browser's localStorage; there is no backend basket entity (not in the data
 * architecture, §8.1) and nothing here is ever sent to a payment provider.
 *
 * Backed by useSyncExternalStore rather than useState+useEffect: localStorage is an external
 * store the server can't see, and this is exactly the case that hook exists for — it avoids the
 * server/client snapshot mismatch without a synchronous setState-in-effect.
 */

export type BasketItem = {
  variantId: string;
  productId: string;
  title: string;
  colour: string;
  size: string;
  price: number;
  sku: string;
  quantity: number;
};

const STORAGE_KEY = "styleseek.basket.v1";
const EMPTY_ITEMS: BasketItem[] = [];
const listeners = new Set<() => void>();
let items: BasketItem[] = EMPTY_ITEMS;

function loadFromStorage(): BasketItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as BasketItem[]) : EMPTY_ITEMS;
  } catch {
    return EMPTY_ITEMS;
  }
}

if (typeof window !== "undefined") {
  items = loadFromStorage();
}

function setItems(next: BasketItem[]) {
  items = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Storage unavailable (private browsing, quota, etc.) — basket just won't persist.
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return items;
}

function getServerSnapshot() {
  return EMPTY_ITEMS;
}

type BasketContextValue = {
  items: BasketItem[];
  addItem: (item: Omit<BasketItem, "quantity">, quantity?: number) => void;
  removeItem: (variantId: string) => void;
  setQuantity: (variantId: string, quantity: number) => void;
  clear: () => void;
  totalItems: number;
  totalPrice: number;
};

const BasketContext = createContext<BasketContextValue | null>(null);

export function BasketProvider({ children }: { children: React.ReactNode }) {
  const currentItems = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const addItem = useCallback((item: Omit<BasketItem, "quantity">, quantity = 1) => {
    const existing = items.find((i) => i.variantId === item.variantId);
    const next = existing
      ? items.map((i) =>
          i.variantId === item.variantId ? { ...i, quantity: i.quantity + quantity } : i,
        )
      : [...items, { ...item, quantity }];
    setItems(next);
  }, []);

  const removeItem = useCallback((variantId: string) => {
    setItems(items.filter((i) => i.variantId !== variantId));
  }, []);

  const setQuantity = useCallback((variantId: string, quantity: number) => {
    setItems(
      quantity <= 0
        ? items.filter((i) => i.variantId !== variantId)
        : items.map((i) => (i.variantId === variantId ? { ...i, quantity } : i)),
    );
  }, []);

  const clear = useCallback(() => setItems(EMPTY_ITEMS), []);

  const totalItems = useMemo(
    () => currentItems.reduce((sum, i) => sum + i.quantity, 0),
    [currentItems],
  );
  const totalPrice = useMemo(
    () => currentItems.reduce((sum, i) => sum + i.price * i.quantity, 0),
    [currentItems],
  );

  const value = useMemo(
    () => ({
      items: currentItems,
      addItem,
      removeItem,
      setQuantity,
      clear,
      totalItems,
      totalPrice,
    }),
    [currentItems, addItem, removeItem, setQuantity, clear, totalItems, totalPrice],
  );

  return <BasketContext.Provider value={value}>{children}</BasketContext.Provider>;
}

export function useBasket(): BasketContextValue {
  const ctx = useContext(BasketContext);
  if (!ctx) {
    throw new Error("useBasket must be used within a BasketProvider");
  }
  return ctx;
}
