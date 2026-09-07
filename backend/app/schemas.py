"""Pydantic response models. Field names and the top-level search response shape follow the
documented contract verbatim — docs/architecture/STYLESEEK_ARCHITECTURE.md §7 example response.
"""

from pydantic import BaseModel


class ProductResult(BaseModel):
    product_id: str
    title: str
    brand: str | None
    category: str
    colour: str
    price: float
    sizes: list[str]
    in_stock: bool
    image_filename: str | None


class QueryInterpretation(BaseModel):
    category: str | None = None
    range: str | None = None
    colour: str | None = None
    occasion: str | None = None
    max_price: float | None = None


class SearchResponse(BaseModel):
    search_request_id: str
    query: str
    interpretation: QueryInterpretation | None
    model_version: str
    fallback_used: bool
    results: list[ProductResult]


class ProductDetail(BaseModel):
    product_id: str
    title: str
    brand: str | None
    category: str
    occasion: str | None
    gender: str | None
    price: float
    image_filename: str | None
    variants: list["ProductVariant"]


class ProductVariant(BaseModel):
    variant_id: str
    colour: str
    size: str
    sku: str
    stock_quantity: int


class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: list[ProductResult]
