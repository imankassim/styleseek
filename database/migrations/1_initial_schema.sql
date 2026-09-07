-- Initial product/variant schema.
-- Entities and key fields per docs/architecture/STYLESEEK_ARCHITECTURE.md §8.1.
-- Constraints implement the data quality gates in §8.3 that a database CAN enforce directly
-- (uniqueness, non-null identifiers, non-negative price/stock, valid FK references).
-- Controlled-vocabulary and image-presence gates are enforced in database/ingest.py instead,
-- since the allowed values depend on what the source dataset actually contains.

CREATE TABLE product (
    product_id          TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    brand               TEXT,
    category            TEXT NOT NULL,
    material            TEXT,
    fit                 TEXT,
    occasion             TEXT,
    description          TEXT,
    price               NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    gender              TEXT,
    source_dataset      TEXT NOT NULL,
    source_row_id       TEXT NOT NULL,
    is_synthetic_price  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE product_variant (
    variant_id           TEXT PRIMARY KEY,
    product_id           TEXT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    colour                TEXT NOT NULL,
    size                  TEXT NOT NULL,
    sku                   TEXT NOT NULL UNIQUE,
    stock_quantity        INTEGER NOT NULL CHECK (stock_quantity >= 0),
    is_synthetic_variant  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, colour, size)
);

CREATE INDEX idx_product_variant_product_id ON product_variant(product_id);
CREATE INDEX idx_product_category ON product(category);
CREATE INDEX idx_product_brand ON product(brand);
