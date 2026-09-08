import type { CategorySummary, Product, ProductDetail, ProductListResponse, ProductVariant } from "@/types/product";
import { apiGet, toProduct, type ApiProduct } from "@/lib/api-client";

type ApiProductListResponse = {
  total: number;
  limit: number;
  offset: number;
  results: ApiProduct[];
};

export type ListProductsParams = {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  inStockOnly?: boolean;
  sort?: "relevance" | "price_asc" | "price_desc";
  limit?: number;
  offset?: number;
};

export async function listProducts(params: ListProductsParams = {}): Promise<ProductListResponse> {
  const data = await apiGet<ApiProductListResponse>("/products", {
    category: params.category,
    min_price: params.minPrice,
    max_price: params.maxPrice,
    in_stock_only: params.inStockOnly,
    sort: params.sort,
    limit: params.limit,
    offset: params.offset,
  });

  return {
    total: data.total,
    limit: data.limit,
    offset: data.offset,
    results: data.results.map(toProduct),
  };
}

type ApiProductVariant = {
  variant_id: string;
  colour: string;
  size: string;
  sku: string;
  stock_quantity: number;
};

type ApiProductDetail = {
  product_id: string;
  title: string;
  brand: string | null;
  category: string;
  occasion: string | null;
  gender: string | null;
  price: number;
  image_filename: string | null;
  variants: ApiProductVariant[];
};

function toVariant(v: ApiProductVariant): ProductVariant {
  return {
    variantId: v.variant_id,
    colour: v.colour,
    size: v.size,
    sku: v.sku,
    stockQuantity: v.stock_quantity,
  };
}

export async function getProduct(productId: string): Promise<ProductDetail> {
  const data = await apiGet<ApiProductDetail>(`/products/${encodeURIComponent(productId)}`);

  return {
    productId: data.product_id,
    title: data.title,
    brand: data.brand,
    category: data.category,
    occasion: data.occasion,
    gender: data.gender,
    price: data.price,
    currency: "GBP",
    imageAlt: `${data.brand ? `${data.brand} ` : ""}${data.title}`,
    variants: data.variants.map(toVariant),
  };
}

type ApiCategoryListResponse = {
  categories: { category: string; product_count: number }[];
};

export async function listCategories(): Promise<CategorySummary[]> {
  const data = await apiGet<ApiCategoryListResponse>("/categories");
  return data.categories.map((c) => ({ category: c.category, productCount: c.product_count }));
}

type ApiSimilarProductsResponse = {
  product_id: string;
  available: boolean;
  results: ApiProduct[];
};

// Visual similarity (architecture §12 journey 16, optional extension — see
// backend/app/visual_similarity.py). `available: false` is a normal, expected response (the
// product has no catalogue image, or the index isn't ready yet) — not an error.
export async function getSimilarProducts(productId: string, limit = 12): Promise<Product[]> {
  const data = await apiGet<ApiSimilarProductsResponse>(
    `/products/${encodeURIComponent(productId)}/similar`,
    { limit }
  );
  return data.available ? data.results.map(toProduct) : [];
}
