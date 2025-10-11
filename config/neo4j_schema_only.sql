// Neo4j Schema - Solo definiciones de esquema (DDL)
// Ejecutar este archivo primero

// Drop the conflicting index first
DROP INDEX judge_name_idx IF EXISTS;

// Constraints
CREATE CONSTRAINT case_process_number_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.process_number IS UNIQUE;
CREATE CONSTRAINT case_sentence_number_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.sentence_number IS UNIQUE;
CREATE CONSTRAINT judge_name_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.name IS UNIQUE;
CREATE CONSTRAINT party_name_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT court_name_unique IF NOT EXISTS FOR (co:Court) REQUIRE co.name IS UNIQUE;
CREATE CONSTRAINT legal_concept_unique IF NOT EXISTS FOR (lc:LegalConcept) REQUIRE lc.concept IS UNIQUE;
CREATE CONSTRAINT legal_problem_unique IF NOT EXISTS FOR (lp:LegalProblem) REQUIRE lp.problem_id IS UNIQUE;
CREATE CONSTRAINT legal_thesis_unique IF NOT EXISTS FOR (lt:LegalThesis) REQUIRE lt.thesis_id IS UNIQUE;
CREATE CONSTRAINT legal_norm_unique IF NOT EXISTS FOR (ln:LegalNorm) REQUIRE ln.norm_id IS UNIQUE;

// Regular Indexes
CREATE INDEX case_process_type_idx IF NOT EXISTS FOR (c:Case) ON (c.process_type);
CREATE INDEX case_provision_type_idx IF NOT EXISTS FOR (c:Case) ON (c.provision_type);
CREATE INDEX case_ruling_direction_idx IF NOT EXISTS FOR (c:Case) ON (c.ruling_direction);
CREATE INDEX case_court_idx IF NOT EXISTS FOR (c:Case) ON (c.court);
CREATE INDEX case_date_idx IF NOT EXISTS FOR (c:Case) ON (c.provision_date);
CREATE INDEX party_type_idx IF NOT EXISTS FOR (p:Party) ON (p.party_type);
CREATE INDEX legal_concept_category_idx IF NOT EXISTS FOR (lc:LegalConcept) ON (lc.category);
CREATE INDEX legal_problem_area_idx IF NOT EXISTS FOR (lp:LegalProblem) ON (lp.legal_area);
CREATE INDEX legal_thesis_area_idx IF NOT EXISTS FOR (lt:LegalThesis) ON (lt.legal_area);
CREATE INDEX legal_norm_type_idx IF NOT EXISTS FOR (ln:LegalNorm) ON (ln.norm_type);

// Fulltext Indexes
CREATE FULLTEXT INDEX case_comprehensive_text IF NOT EXISTS FOR (c:Case) ON EACH [
    c.relevant_facts, 
    c.legal_problem, 
    c.legal_thesis, 
    c.extract,
    c.dissenting_thesis,
    c.dissenting_extract,
    c.clarifying_thesis,
    c.clarifying_extract
];

CREATE FULLTEXT INDEX legal_problem_text IF NOT EXISTS FOR (lp:LegalProblem) ON EACH [lp.problem_text];
CREATE FULLTEXT INDEX legal_thesis_text IF NOT EXISTS FOR (lt:LegalThesis) ON EACH [lt.thesis_text];
CREATE FULLTEXT INDEX legal_concept_text IF NOT EXISTS FOR (lc:LegalConcept) ON EACH [lc.concept, lc.description];

// Vector Index
CREATE VECTOR INDEX case_enhanced_embeddings IF NOT EXISTS FOR (c:Case) ON (c.similarity_vector)
OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};
