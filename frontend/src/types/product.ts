/**
 * Shared with the documented `/search` response contract
 * (docs/architecture/STYLESEEK_ARCHITECTURE.md §7). The frontend commits to this shape now,
 * before the real API exists, so later stages (5: connect the application) swap the data
 * source without changing the UI.
 */

export type Product = {
  productId: string;
  title: string;
  brand: string;
  category: string;
  colour: string;
  price: number;
  currency: "GBP";
  sizes: string[];
  inStock: boolean;
  imageAlt: string;
};

export type QueryInterpretation = {
  category: string | null;
  range: string | null;
  colour: string | null;
  occasion: string | null;
  maxPrice: number | null;
} | null;

export type SearchResponse = {
  searchRequestId: string;
  query: string;
  interpretation: QueryInterpretation;
  modelVersion: string;
  fallbackUsed: boolean;
  results: Product[];
};
