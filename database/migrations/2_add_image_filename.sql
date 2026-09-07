-- Local image reference from the source dataset. Not proof of licence to display publicly —
-- see docs/data_sheets/catalogue_data_sheet.md, the licence-confirmation gate is still open.
-- Nullable: a handful of source rows have no corresponding image file.

ALTER TABLE product ADD COLUMN image_filename TEXT;
