import type { Product, SearchResponse } from "@/types/product";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type ApiProduct = {
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

type ApiSearchResponse = {
  search_request_id: string;
  query: string;
  interpretation: {
    category: string | null;
    range: string | null;
    colour: string | null;
    occasion: string | null;
    max_price: number | null;
  } | null;
  model_version: string;
  fallback_used: boolean;
  results: ApiProduct[];
};

function toProduct(p: ApiProduct): Product {
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

export async function searchProducts(query: string): Promise<SearchResponse> {
  const url = new URL("/search", API_BASE_URL);
  url.searchParams.set("q", query);

  const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) {
    throw new Error(`Search request failed (${response.status}).`);
  }

  const data: ApiSearchResponse = await response.json();

  return {
    searchRequestId: data.search_request_id,
    query: data.query,
    interpretation: data.interpretation
      ? {
          category: data.interpretation.category,
          range: data.interpretation.range,
          colour: data.interpretation.colour,
          occasion: data.interpretation.occasion,
          maxPrice: data.interpretation.max_price,
        }
      : null,
    modelVersion: data.model_version,
    fallbackUsed: data.fallback_used,
    results: data.results.map(toProduct),
  };
}
