// Step 1: Find all existing indexes
SHOW INDEXES;

// Step 2: If you see an index like "(:Judge {name})" in the output above,
// copy its exact name and run:
// DROP INDEX <exact_index_name>;

// Step 3: Common manual commands to try:
DROP INDEX `(:Judge {name})` IF EXISTS;
DROP INDEX `(:Party {name})` IF EXISTS;
DROP INDEX `(:Court {name})` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})` IF EXISTS;

// Step 4: Try with different quote styles
DROP INDEX `(:Judge {name})` IF EXISTS;
DROP INDEX `(:Party {name})` IF EXISTS;
DROP INDEX `(:Court {name})` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})` IF EXISTS;

// Step 5: Try with single quotes
DROP INDEX '(:Judge {name})' IF EXISTS;
DROP INDEX '(:Party {name})' IF EXISTS;
DROP INDEX '(:Court {name})' IF EXISTS;
DROP INDEX '(:LegalConcept {concept})' IF EXISTS;
