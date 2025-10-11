// Simple cleanup script - run this first
// This will show you what indexes exist and help you drop them

// Step 1: Show all existing indexes
SHOW INDEXES;

// Step 2: Show all existing constraints  
SHOW CONSTRAINTS;

// Step 3: Drop the specific problematic index
DROP INDEX judge_name_idx IF EXISTS;

// Step 4: Try to drop other common problematic indexes
DROP INDEX `(:Judge {name})` IF EXISTS;
DROP INDEX `(:Party {name})` IF EXISTS;
DROP INDEX `(:Court {name})` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})` IF EXISTS;

// Step 5: If you see other indexes in SHOW INDEXES output above,
// drop them using their exact names
// Example: DROP INDEX party_name_idx IF EXISTS;


// Step 4: If the above don't work, look at the SHOW INDEXES output above
// and manually drop the exact index name you see there
// Example: DROP INDEX index_abc123 IF EXISTS;



// Step 4: If the above don't work, look at the SHOW INDEXES output above
// and manually drop the exact index name you see there
// Example: DROP INDEX index_abc123 IF EXISTS;
