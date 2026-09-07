import type { SearchResponse } from "@/types/product";
import { apiGet, toProduct, type ApiProduct } from "@/lib/api-client";

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

export async function searchProducts(query: string): Promise<SearchResponse> {
  const data = await apiGet<ApiSearchResponse>("/search", { q: query });

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
