import type { Product } from "@/types/product";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ApiProduct = {
  product_id: string;
  title: string;
  brand: string | null;
  category: string;
  colour: string;
  price: number;
  sizes: string[];
  in_stock: boolean;
  image_filename: string | null;
};

export function toProduct(p: ApiProduct): Product {
  return {
    productId: p.product_id,
    title: p.title,
    brand: p.brand,
    category: p.category,
    colour: p.colour,
    price: p.price,
    currency: "GBP",
    sizes: p.sizes,
    inStock: p.in_stock,
    imageAlt: `${p.brand ? `${p.brand} ` : ""}${p.title}`,
  };
}

export async function apiGet<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed (${response.status}).`);
  }
  return response.json();
}
