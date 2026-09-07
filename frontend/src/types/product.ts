/**
 * Shared with the documented `/search` response contract
 * (docs/architecture/STYLESEEK_ARCHITECTURE.md §7). Populated from the real FastAPI backend
 * (see src/lib/search-api.ts) as of Stage 5.
 */

export type Product = {
  productId: string;
  title: string;
  brand: string | null;
  category: string;
  colour: string;
  price: number;
  currency: "GBP";
  sizes: string[];
  inStock: boolean;
  // Derived from title/brand, not the real dataset photo — the catalogue's image licence isn't
  // confirmed yet (docs/data_sheets/catalogue_data_sheet.md), so the UI still shows a
  // placeholder block rather than serving real images.
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

export type ProductVariant = {
  variantId: string;
  colour: string;
  size: string;
  sku: string;
  stockQuantity: number;
};

export type ProductDetail = {
  productId: string;
  title: string;
  brand: string | null;
  category: string;
  occasion: string | null;
  gender: string | null;
  price: number;
  currency: "GBP";
  imageAlt: string;
  variants: ProductVariant[];
};

export type ProductListResponse = {
  total: number;
  limit: number;
  offset: number;
  results: Product[];
};

export type CategorySummary = {
  category: string;
  productCount: number;
};
