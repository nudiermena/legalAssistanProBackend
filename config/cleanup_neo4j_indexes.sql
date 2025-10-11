// Cleanup script for Neo4j indexes and constraints
// Run this first before running the main schema

// Drop all constraints first
DROP CONSTRAINT case_process_number_unique IF EXISTS;
DROP CONSTRAINT case_sentence_number_unique IF EXISTS;
DROP CONSTRAINT party_name_unique IF EXISTS;
DROP CONSTRAINT court_name_unique IF EXISTS;
DROP CONSTRAINT judge_name_unique IF EXISTS;
DROP CONSTRAINT legal_concept_unique IF EXISTS;
DROP CONSTRAINT legal_problem_unique IF EXISTS;
DROP CONSTRAINT legal_thesis_unique IF EXISTS;
DROP CONSTRAINT legal_norm_unique IF EXISTS;

// Try to drop indexes with various possible names
DROP INDEX `(:Judge {name})` IF EXISTS;
DROP INDEX `(:Party {name})` IF EXISTS;
DROP INDEX `(:Court {name})` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})` IF EXISTS;

// Try common auto-generated index names
DROP INDEX judge_name_unique IF EXISTS;
DROP INDEX party_name_unique IF EXISTS;
DROP INDEX court_name_unique IF EXISTS;
DROP INDEX legal_concept_unique IF EXISTS;

// Try to drop indexes with common auto-generated names
DROP INDEX `(:Judge {name})` IF EXISTS;
DROP INDEX `(:Party {name})` IF EXISTS;
DROP INDEX `(:Court {name})` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})` IF EXISTS;

// Try to drop indexes with numeric suffixes
DROP INDEX `(:Judge {name})_1` IF EXISTS;
DROP INDEX `(:Judge {name})_2` IF EXISTS;
DROP INDEX `(:Judge {name})_3` IF EXISTS;
DROP INDEX `(:Party {name})_1` IF EXISTS;
DROP INDEX `(:Party {name})_2` IF EXISTS;
DROP INDEX `(:Court {name})_1` IF EXISTS;
DROP INDEX `(:Court {name})_2` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})_1` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})_2` IF EXISTS;

// Try to drop indexes with timestamp suffixes
DROP INDEX `(:Judge {name})_timestamp` IF EXISTS;
DROP INDEX `(:Party {name})_timestamp` IF EXISTS;
DROP INDEX `(:Court {name})_timestamp` IF EXISTS;
DROP INDEX `(:LegalConcept {concept})_timestamp` IF EXISTS;
