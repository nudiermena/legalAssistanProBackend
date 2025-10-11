import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from neo4j import GraphDatabase

try:
    from config.settings import (
        NEO4J_URI,
        NEO4J_USERNAME,
        NEO4J_PASSWORD,
        NEO4J_DATABASE,
    )
except Exception:
    # Fallbacks if settings not present
    NEO4J_URI = None
    NEO4J_USERNAME = None
    NEO4J_PASSWORD = None
    NEO4J_DATABASE = None


logger = logging.getLogger(__name__)


@dataclass
class GraphInsight:
    """Simple container for graph-derived insights."""
    type: str
    data: Dict[str, Any]


class Neo4jKnowledgeGraph:
    """Lightweight Neo4j access wrapper for RAG over legal data."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, database: Optional[str] = None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USERNAME
        self.password = password or NEO4J_PASSWORD
        self.database = database or NEO4J_DATABASE
        self.driver = None

        if self.uri and self.user and self.password:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                logger.info("Neo4j driver initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j driver: {e}")
                self.driver = None
        else:
            logger.warning("Neo4j credentials not configured; graph features disabled")

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def _session(self):
        if not self.driver:
            return None
        try:
            return self.driver.session(database=self.database) if self.database else self.driver.session()
        except Exception:
            return self.driver.session()

    # ------------------------
    # Schema initialization
    # ------------------------
    def setup_constraints_and_indexes(self) -> None:
        """Create constraints and indexes for optimal performance."""
        if not self.driver:
            logger.warning("Neo4j not configured; skipping schema setup")
            return

        statements = [
            # Unique constraints
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE",
            "CREATE CONSTRAINT court_id_unique IF NOT EXISTS FOR (co:Court) REQUIRE co.court_id IS UNIQUE",
            "CREATE CONSTRAINT judge_id_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.judge_id IS UNIQUE",
            "CREATE CONSTRAINT law_id_unique IF NOT EXISTS FOR (l:Law) REQUIRE l.law_id IS UNIQUE",
            "CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.party_id IS UNIQUE",

            # Indexes
            "CREATE INDEX case_date_idx IF NOT EXISTS FOR (c:Case) ON (c.filing_date)",
            "CREATE INDEX case_outcome_idx IF NOT EXISTS FOR (c:Case) ON (c.outcome)",
            "CREATE INDEX case_jurisdiction_idx IF NOT EXISTS FOR (c:Case) ON (c.jurisdiction)",
            "CREATE INDEX law_type_idx IF NOT EXISTS FOR (l:Law) ON (l.law_type)",
            "CREATE INDEX precedent_weight_idx IF NOT EXISTS FOR (c:Case) ON (c.precedent_value)",

            # Fulltext indexes
            "CREATE FULLTEXT INDEX case_content_text IF NOT EXISTS FOR (c:Case) ON EACH [c.summary, c.legal_issue, c.ruling_text]",
            "CREATE FULLTEXT INDEX law_content_text IF NOT EXISTS FOR (l:Law) ON EACH [l.title, l.content_summary]",
        ]

        with self._session() as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                    logger.info(f"Applied: {stmt}")
                except Exception as e:
                    logger.warning(f"Skipped (already exists?): {e}")

    def create_core_schema(self) -> None:
        """Create core Colombian legal nodes and relationships."""
        if not self.driver:
            logger.warning("Neo4j not configured; skipping core schema creation")
            return

        core_nodes = [
            # Courts
            """
            MERGE (cc:Court {court_id:'constitutional_court'})
            SET cc.name='Corte Constitucional', cc.level='supreme', cc.jurisdiction='constitutional', cc.location='Bogotá'
            """,
            """
            MERGE (sc:Court {court_id:'supreme_court'})
            SET sc.name='Corte Suprema de Justicia', sc.level='supreme', sc.jurisdiction='ordinary', sc.location='Bogotá'
            """,
            """
            MERGE (cs:Court {court_id:'council_of_state'})
            SET cs.name='Consejo de Estado', cs.level='supreme', cs.jurisdiction='administrative', cs.location='Bogotá'
            """,

            # Laws
            """
            MERGE (constitution:Law {law_id:'constitution_1991'})
            SET constitution.title='Constitución Política de Colombia', constitution.law_type='constitutional', constitution.status='active', constitution.hierarchy_level=1
            """,
            """
            MERGE (penal:Law {law_id:'penal_code_2000'})
            SET penal.title='Código Penal - Ley 599 de 2000', penal.law_type='penal', penal.status='active', penal.hierarchy_level=2
            """,
            """
            MERGE (civil:Law {law_id:'civil_code_1873'})
            SET civil.title='Código Civil Colombiano', civil.law_type='civil', civil.status='active', civil.hierarchy_level=2
            """,

            # Legal Areas
            """
            MERGE (constitutional_law:LegalArea {area_id:'constitutional_law'})
            SET constitutional_law.name='Derecho Constitucional', constitutional_law.complexity_level='high'
            """,
            """
            MERGE (criminal_law:LegalArea {area_id:'criminal_law'})
            SET criminal_law.name='Derecho Penal', criminal_law.complexity_level='high'
            """,
            """
            MERGE (civil_law:LegalArea {area_id:'civil_law'})
            SET civil_law.name='Derecho Civil', civil_law.complexity_level='medium'
            """,
            """
            MERGE (administrative_law:LegalArea {area_id:'administrative_law'})
            SET administrative_law.name='Derecho Administrativo', administrative_law.complexity_level='medium'
            """,

            # Legal Concepts
            """
            MERGE (due_process:LegalConcept {concept_id:'due_process'})
            SET due_process.name='Debido Proceso', due_process.importance_score=0.98, due_process.legal_source='constitution_1991'
            """,
            """
            MERGE (fundamental_rights:LegalConcept {concept_id:'fundamental_rights'})
            SET fundamental_rights.name='Derechos Fundamentales', fundamental_rights.importance_score=0.95, fundamental_rights.legal_source='constitution_1991'
            """,

            # Procedure Types
            """
            MERGE (tutela:ProcedureType {procedure_id:'tutela'})
            SET tutela.name='Acción de Tutela', tutela.jurisdiction='constitutional', tutela.time_limit_days=10
            """,
            """
            MERGE (cassation:ProcedureType {procedure_id:'cassation'})
            SET cassation.name='Recurso de Casación', cassation.jurisdiction='ordinary', cassation.time_limit_days=30
            """,
        ]

        relationships = [
            # Court coordination
            """
            MATCH (cc:Court {court_id:'constitutional_court'}), (sc:Court {court_id:'supreme_court'}), (cs:Court {court_id:'council_of_state'})
            MERGE (cc)-[:COORDINATES_WITH]->(sc)
            MERGE (cc)-[:COORDINATES_WITH]->(cs)
            MERGE (sc)-[:COORDINATES_WITH]->(cs)
            """,
            # Law hierarchy
            """
            MATCH (constitution:Law {law_id:'constitution_1991'}), (penal:Law {law_id:'penal_code_2000'}), (civil:Law {law_id:'civil_code_1873'})
            MERGE (constitution)-[:HIERARCHICALLY_SUPERIOR_TO]->(penal)
            MERGE (constitution)-[:HIERARCHICALLY_SUPERIOR_TO]->(civil)
            """,
            # Area to concept
            """
            MATCH (area:LegalArea {area_id:'constitutional_law'}), (c1:LegalConcept {concept_id:'fundamental_rights'}), (c2:LegalConcept {concept_id:'due_process'})
            MERGE (area)-[:CONTAINS_CONCEPT]->(c1)
            MERGE (area)-[:CONTAINS_CONCEPT]->(c2)
            """,
        ]

        with self._session() as session:
            for stmt in core_nodes:
                try:
                    session.run(stmt)
                except Exception as e:
                    logger.warning(f"Node init issue: {e}")
            for stmt in relationships:
                try:
                    session.run(stmt)
                except Exception as e:
                    logger.warning(f"Rel init issue: {e}")

    def initialize_full_schema(self) -> None:
        """Public entry to create constraints, indexes, nodes, and relationships."""
        self.setup_constraints_and_indexes()
        self.create_core_schema()

    # ------------------------
    # Extended design from spec
    # ------------------------
    def create_extended_design(self, vector_dimensions: int = 768) -> None:
        """Create additional entities, relationships, and indexes per design doc."""
        if not self.driver:
            logger.warning("Neo4j not configured; skipping extended design creation")
            return

        with self._session() as session:
            # Uniqueness constraints for new entities
            constraints = [
                "CREATE CONSTRAINT lawyer_id_unique IF NOT EXISTS FOR (l:Lawyer) REQUIRE l.lawyer_id IS UNIQUE",
                "CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.party_id IS UNIQUE",
                "CREATE CONSTRAINT statute_id_unique IF NOT EXISTS FOR (s:Statute) REQUIRE s.statute_id IS UNIQUE",
                "CREATE CONSTRAINT precedent_id_unique IF NOT EXISTS FOR (pr:Precedent) REQUIRE pr.precedent_id IS UNIQUE",
                "CREATE CONSTRAINT citation_id_unique IF NOT EXISTS FOR (ci:Citation) REQUIRE ci.citation_id IS UNIQUE",
                "CREATE CONSTRAINT jurisdiction_id_unique IF NOT EXISTS FOR (jz:Jurisdiction) REQUIRE jz.jurisdiction_id IS UNIQUE",
                "CREATE CONSTRAINT case_type_id_unique IF NOT EXISTS FOR (ct:CaseType) REQUIRE ct.case_type_id IS UNIQUE",
                "CREATE CONSTRAINT legal_issue_id_unique IF NOT EXISTS FOR (li:LegalIssue) REQUIRE li.issue_id IS UNIQUE",
                "CREATE CONSTRAINT motion_id_unique IF NOT EXISTS FOR (m:Motion) REQUIRE m.motion_id IS UNIQUE",
                "CREATE CONSTRAINT ruling_id_unique IF NOT EXISTS FOR (r:Ruling) REQUIRE r.ruling_id IS UNIQUE",
                "CREATE CONSTRAINT appeal_id_unique IF NOT EXISTS FOR (a:Appeal) REQUIRE a.appeal_id IS UNIQUE",
                "CREATE CONSTRAINT timeframe_id_unique IF NOT EXISTS FOR (t:TimeFrame) REQUIRE t.timeframe_id IS UNIQUE",
                "CREATE CONSTRAINT legaltopic_id_unique IF NOT EXISTS FOR (lt:LegalTopic) REQUIRE lt.topic_id IS UNIQUE",
                "CREATE CONSTRAINT outcome_id_unique IF NOT EXISTS FOR (o:Outcome) REQUIRE o.outcome_id IS UNIQUE",
                "CREATE CONSTRAINT authority_id_unique IF NOT EXISTS FOR (la:LegalAuthority) REQUIRE la.authority_id IS UNIQUE",
                "CREATE CONSTRAINT partytype_id_unique IF NOT EXISTS FOR (pt:PartyType) REQUIRE pt.party_type_id IS UNIQUE",
                "CREATE CONSTRAINT profession_id_unique IF NOT EXISTS FOR (lp:LegalProfession) REQUIRE lp.profession_id IS UNIQUE",
                "CREATE CONSTRAINT documenttype_id_unique IF NOT EXISTS FOR (dt:DocumentType) REQUIRE dt.document_type_id IS UNIQUE",
                "CREATE CONSTRAINT settlement_id_unique IF NOT EXISTS FOR (st:Settlement) REQUIRE st.settlement_id IS UNIQUE",
            ]
            for c in constraints:
                try:
                    session.run(c)
                except Exception as e:
                    logger.warning(f"Constraint skip: {e}")

            # Indexes frequently used
            indexes = [
                "CREATE INDEX case_number_idx IF NOT EXISTS FOR (c:Case) ON (c.case_number)",
                "CREATE INDEX judge_name_idx IF NOT EXISTS FOR (j:Judge) ON (j.name)",
                "CREATE INDEX lawyer_name_idx IF NOT EXISTS FOR (l:Lawyer) ON (l.name)",
                "CREATE INDEX concept_name_idx IF NOT EXISTS FOR (lc:LegalConcept) ON (lc.name)",
                "CREATE INDEX statute_title_idx IF NOT EXISTS FOR (s:Statute) ON (s.title)",
                "CREATE INDEX outcome_type_idx IF NOT EXISTS FOR (o:Outcome) ON (o.type)",
                "CREATE INDEX jurisdiction_name_idx IF NOT EXISTS FOR (jz:Jurisdiction) ON (jz.name)",
                "CREATE INDEX case_type_idx IF NOT EXISTS FOR (ct:CaseType) ON (ct.name)",
            ]
            for i in indexes:
                try:
                    session.run(i)
                except Exception as e:
                    logger.warning(f"Index skip: {e}")

            # Vector index (Neo4j 5+)
            try:
                session.run(
                    """
                    CREATE VECTOR INDEX case_embeddings IF NOT EXISTS FOR (c:Case) ON (c.similarity_vector)
                    OPTIONS {indexConfig: {`vector.dimensions`: $dims, `vector.similarity_function`: 'cosine'}}
                    """,
                    {"dims": vector_dimensions},
                )
            except Exception as e:
                logger.warning(f"Vector index skip: {e}")

            # Seed taxonomy nodes minimally (Outcome, CaseType examples)
            seeds = [
                "MERGE (:Outcome {outcome_id:'favorable', type:'favorable'})",
                "MERGE (:Outcome {outcome_id:'unfavorable', type:'unfavorable'})",
                "MERGE (:Outcome {outcome_id:'partially_favorable', type:'partially_favorable'})",
                "MERGE (:CaseType {case_type_id:'tutela', name:'Tutela'})",
                "MERGE (:CaseType {case_type_id:'civil_ordinary', name:'Civil ordinario'})",
            ]
            for s in seeds:
                try:
                    session.run(s)
                except Exception:
                    pass

    # ------------------------
    # Upsert helpers (idempotent)
    # ------------------------
    def upsert_case(self, case: Dict[str, Any]) -> None:
        if not self.driver:
            return
        query = """
        MERGE (c:Case {case_id:$case.case_id})
        SET c += $case
        """
        with self._session() as session:
            session.run(query, {"case": case})

    def upsert_judge(self, judge: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (j:Judge {judge_id:$id}) SET j += $props", {"id": judge.get("judge_id"), "props": judge})

    def upsert_lawyer(self, lawyer: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (l:Lawyer {lawyer_id:$id}) SET l += $props", {"id": lawyer.get("lawyer_id"), "props": lawyer})

    def upsert_party(self, party: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (p:Party {party_id:$id}) SET p += $props", {"id": party.get("party_id"), "props": party})

    def upsert_statute(self, statute: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (s:Statute {statute_id:$id}) SET s += $props", {"id": statute.get("statute_id"), "props": statute})

    def upsert_concept(self, concept: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (lc:LegalConcept {concept_id:$id}) SET lc += $props", {"id": concept.get("concept_id"), "props": concept})

    # Extended entity upserts
    def upsert_law(self, law: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (l:Law {law_id:$id}) SET l += $props", {"id": law.get("law_id"), "props": law})

    def upsert_document(self, document: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (d:LegalDocument {document_id:$id}) SET d += $props", {"id": document.get("document_id"), "props": document})

    def upsert_evidence(self, evidence: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (e:Evidence {evidence_id:$id}) SET e += $props", {"id": evidence.get("evidence_id"), "props": evidence})

    def upsert_witness(self, witness: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (w:Witness {witness_id:$id}) SET w += $props", {"id": witness.get("witness_id"), "props": witness})

    def upsert_hearing(self, hearing: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (h:Hearing {hearing_id:$id}) SET h += $props", {"id": hearing.get("hearing_id"), "props": hearing})

    def upsert_appeal(self, appeal: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (a:Appeal {appeal_id:$id}) SET a += $props", {"id": appeal.get("appeal_id"), "props": appeal})

    def upsert_jurisdiction(self, jz: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (j:Jurisdiction {jurisdiction_id:$id}) SET j += $props", {"id": jz.get("jurisdiction_id"), "props": jz})

    def upsert_case_type(self, case_type: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (ct:CaseType {case_type_id:$id}) SET ct += $props", {"id": case_type.get("case_type_id"), "props": case_type})

    def upsert_legal_issue(self, issue: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (li:LegalIssue {issue_id:$id}) SET li += $props", {"id": issue.get("issue_id"), "props": issue})

    def upsert_demand_type(self, demand: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (dt:DemandType {demand_type_id:$id}) SET dt += $props", {"id": demand.get("demand_type_id"), "props": demand})

    def upsert_legal_authority(self, authority: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (la:LegalAuthority {authority_id:$id}) SET la += $props", {"id": authority.get("authority_id"), "props": authority})

    def upsert_party_type(self, party_type: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (pt:PartyType {party_type_id:$id}) SET pt += $props", {"id": party_type.get("party_type_id"), "props": party_type})

    def upsert_legal_profession(self, profession: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (lp:LegalProfession {profession_id:$id}) SET lp += $props", {"id": profession.get("profession_id"), "props": profession})

    def upsert_document_type(self, doc_type: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (dt:DocumentType {document_type_id:$id}) SET dt += $props", {"id": doc_type.get("document_type_id"), "props": doc_type})

    def upsert_settlement(self, settlement: Dict[str, Any]) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run("MERGE (st:Settlement {settlement_id:$id}) SET st += $props", {"id": settlement.get("settlement_id"), "props": settlement})

    # ------------------------
    # Relationship creators
    # ------------------------
    def relate_case_cites(self, source_case_id: str, target_case_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (a:Case {case_id:$a}), (b:Case {case_id:$b})
                MERGE (a)-[r:CITES]->(b)
                SET r += $props
                """,
                {"a": source_case_id, "b": target_case_id, "props": props or {}},
            )

    def relate_case_follows_precedent(self, case_id: str, precedent_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (p:Precedent {precedent_id:$pid})
                MERGE (c)-[r:FOLLOWS_PRECEDENT]->(p)
                SET r += $props
                """,
                {"cid": case_id, "pid": precedent_id, "props": props or {}},
            )

    def relate_case_involves_concept(self, case_id: str, concept_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (lc:LegalConcept {concept_id:$ccid})
                MERGE (c)-[r:INVOLVES]->(lc)
                SET r += $props
                """,
                {"cid": case_id, "ccid": concept_id, "props": props or {}},
            )

    def relate_case_interprets_statute(self, case_id: str, statute_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (s:Statute {statute_id:$sid})
                MERGE (c)-[r:INTERPRETS]->(s)
                SET r += $props
                """,
                {"cid": case_id, "sid": statute_id, "props": props or {}},
            )

    def relate_case_resulted_in(self, case_id: str, outcome_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (o:Outcome {outcome_id:$oid})
                MERGE (c)-[:RESULTED_IN]->(o)
                """,
                {"cid": case_id, "oid": outcome_id},
            )

    # Additional relationship helpers per documentation
    def relate_case_has_party(self, case_id: str, party_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (p:Party {party_id:$pid})
                MERGE (c)-[r:HAS_PARTY]->(p)
                SET r += $props
                """,
                {"cid": case_id, "pid": party_id, "props": props or {}},
            )

    def relate_case_contains_document(self, case_id: str, document_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (d:LegalDocument {document_id:$did})
                MERGE (c)-[r:CONTAINS_DOCUMENT]->(d)
                SET r += $props
                """,
                {"cid": case_id, "did": document_id, "props": props or {}},
            )

    def relate_document_filed_by(self, document_id: str, party_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (d:LegalDocument {document_id:$did}), (p:Party {party_id:$pid})
                MERGE (d)-[r:FILED_BY]->(p)
                SET r += $props
                """,
                {"did": document_id, "pid": party_id, "props": props or {}},
            )

    def relate_document_served_to(self, document_id: str, party_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (d:LegalDocument {document_id:$did}), (p:Party {party_id:$pid})
                MERGE (d)-[r:SERVED_TO]->(p)
                SET r += $props
                """,
                {"did": document_id, "pid": party_id, "props": props or {}},
            )

    def relate_case_includes_evidence(self, case_id: str, evidence_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (e:Evidence {evidence_id:$eid})
                MERGE (c)-[r:INCLUDES_EVIDENCE]->(e)
                SET r += $props
                """,
                {"cid": case_id, "eid": evidence_id, "props": props or {}},
            )

    def relate_case_has_precedent(self, case_id: str, precedent_case_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (p:Case {case_id:$pid})
                MERGE (c)-[r:HAS_PRECEDENT]->(p)
                SET r += $props
                """,
                {"cid": case_id, "pid": precedent_case_id, "props": props or {}},
            )

    def relate_cases_similar_to(self, a_id: str, b_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (a:Case {case_id:$a}), (b:Case {case_id:$b})
                MERGE (a)-[r:SIMILAR_TO]->(b)
                SET r += $props
                """,
                {"a": a_id, "b": b_id, "props": props or {}},
            )

    def relate_case_presided_by(self, case_id: str, judge_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (j:Judge {judge_id:$jid})
                MERGE (c)-[r:PRESIDED_BY]->(j)
                SET r += $props
                """,
                {"cid": case_id, "jid": judge_id, "props": props or {}},
            )

    def relate_case_decided_by(self, case_id: str, judge_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (j:Judge {judge_id:$jid})
                MERGE (c)-[r:DECIDED_BY]->(j)
                SET r += $props
                """,
                {"cid": case_id, "jid": judge_id, "props": props or {}},
            )

    def relate_party_represented_by(self, party_id: str, lawyer_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (p:Party {party_id:$pid}), (l:Lawyer {lawyer_id:$lid})
                MERGE (p)-[r:REPRESENTED_BY]->(l)
                SET r += $props
                """,
                {"pid": party_id, "lid": lawyer_id, "props": props or {}},
            )

    def relate_case_heard_in(self, case_id: str, court_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (ct:Court {court_id:$coid})
                MERGE (c)-[:HEARD_IN]->(ct)
                """,
                {"cid": case_id, "coid": court_id},
            )

    def relate_case_under_jurisdiction(self, case_id: str, jurisdiction_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (c:Case {case_id:$cid}), (jz:Jurisdiction {jurisdiction_id:$jid})
                MERGE (c)-[:UNDER_JURISDICTION]->(jz)
                """,
                {"cid": case_id, "jid": jurisdiction_id},
            )

    def relate_court_appeals_to(self, lower_court_id: str, higher_court_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (l:Court {court_id:$l}), (h:Court {court_id:$h})
                MERGE (l)-[:APPEALS_TO]->(h)
                """,
                {"l": lower_court_id, "h": higher_court_id},
            )

    def relate_case_appeals(self, from_case_id: str, to_case_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (a:Case {case_id:$a}), (b:Case {case_id:$b})
                MERGE (a)-[:APPEALS]->(b)
                """,
                {"a": from_case_id, "b": to_case_id},
            )

    def relate_case_remands(self, from_case_id: str, to_case_id: str) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                """
                MATCH (a:Case {case_id:$a}), (b:Case {case_id:$b})
                MERGE (a)-[:REMANDS]->(b)
                """,
                {"a": from_case_id, "b": to_case_id},
            )

    # Court hierarchy relationships
    def relate_court_superior_to(self, lower_court_id: str, higher_court_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (l:Court {court_id:$l}), (h:Court {court_id:$h}) MERGE (l)-[r:HIERARCHICALLY_SUPERIOR_TO]->(h) SET r += $props",
                {"l": lower_court_id, "h": higher_court_id, "props": props or {}},
            )

    # Law modification relationships
    def relate_law_modifies(self, law_id: str, target_law_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (a:Law {law_id:$a}), (b:Law {law_id:$b}) MERGE (a)-[r:MODIFIES]->(b) SET r += $props",
                {"a": law_id, "b": target_law_id, "props": props or {}},
            )

    def relate_law_repeals(self, law_id: str, target_law_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (a:Law {law_id:$a}), (b:Law {law_id:$b}) MERGE (a)-[r:REPEALS]->(b) SET r += $props",
                {"a": law_id, "b": target_law_id, "props": props or {}},
            )

    # Concept defined_by law
    def relate_concept_defined_by(self, concept_id: str, law_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (c:LegalConcept {concept_id:$c}), (l:Law {law_id:$l}) MERGE (c)-[r:DEFINED_BY]->(l) SET r += $props",
                {"c": concept_id, "l": law_id, "props": props or {}},
            )

    # Document cross-links
    def relate_document_amends(self, doc_id: str, target_doc_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (a:LegalDocument {document_id:$a}), (b:LegalDocument {document_id:$b}) MERGE (a)-[r:AMENDS]->(b) SET r += $props",
                {"a": doc_id, "b": target_doc_id, "props": props or {}},
            )

    def relate_document_responds_to(self, doc_id: str, target_doc_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (a:LegalDocument {document_id:$a}), (b:LegalDocument {document_id:$b}) MERGE (a)-[r:RESPONDS_TO]->(b) SET r += $props",
                {"a": doc_id, "b": target_doc_id, "props": props or {}},
            )

    # Hearing attendance
    def relate_hearing_attended_by_party(self, hearing_id: str, party_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (h:Hearing {hearing_id:$h}), (p:Party {party_id:$p}) MERGE (h)-[r:ATTENDED_BY]->(p) SET r += $props",
                {"h": hearing_id, "p": party_id, "props": props or {}},
            )

    def relate_hearing_presided_by(self, hearing_id: str, judge_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (h:Hearing {hearing_id:$h}), (j:Judge {judge_id:$j}) MERGE (h)-[r:PRESIDED_BY]->(j) SET r += $props",
                {"h": hearing_id, "j": judge_id, "props": props or {}},
            )

    # Appeals
    def relate_case_subject_to_appeal(self, case_id: str, appeal_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (c:Case {case_id:$c}), (a:Appeal {appeal_id:$a}) MERGE (c)-[r:SUBJECT_TO_APPEAL]->(a) SET r += $props",
                {"c": case_id, "a": appeal_id, "props": props or {}},
            )

    def relate_appeal_decided_by_court(self, appeal_id: str, court_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (a:Appeal {appeal_id:$a}), (ct:Court {court_id:$ct}) MERGE (a)-[r:DECIDED_BY]->(ct) SET r += $props",
                {"a": appeal_id, "ct": court_id, "props": props or {}},
            )

    # Judge recusal
    def relate_judge_recused_from(self, judge_id: str, case_id: str, props: Optional[Dict[str, Any]] = None) -> None:
        if not self.driver:
            return
        with self._session() as session:
            session.run(
                "MATCH (j:Judge {judge_id:$j}), (c:Case {case_id:$c}) MERGE (j)-[r:RECUSED_FROM]->(c) SET r += $props",
                {"j": judge_id, "c": case_id, "props": props or {}},
            )


    def find_similar_cases(self, legal_area: str, procedure_type: Optional[str], legal_concepts: List[str], court_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find cases similar to provided features."""
        if not self.driver:
            return []

        query = """
        MATCH (c:Case)
        WHERE c.legal_area = $legal_area
          AND ($procedure_type IS NULL OR c.procedure_type = $procedure_type)
        WITH c,
             (CASE WHEN size($legal_concepts)=0 THEN 0.0 ELSE size([x IN $legal_concepts WHERE x IN c.legal_concepts]) * 1.0 / size($legal_concepts) END) AS concept_similarity,
             (CASE WHEN $court_id IS NULL THEN 0.8 WHEN c.court_id = $court_id THEN 1.0 ELSE 0.7 END) AS court_similarity
        WITH c, (concept_similarity * 0.6 + court_similarity * 0.4) AS overall_similarity
        WHERE overall_similarity > 0.3
        RETURN c.case_id AS case_id,
               c.title AS title,
               c.outcome AS outcome,
               c.court_id AS court_id,
               c.filing_date AS filing_date,
               overall_similarity AS similarity
        ORDER BY overall_similarity DESC
        LIMIT $limit
        """

        with self._session() as session:
            result = session.run(
                query,
                {
                    "legal_area": legal_area,
                    "procedure_type": procedure_type,
                    "legal_concepts": legal_concepts or [],
                    "court_id": court_id,
                    "limit": limit,
                },
            )
            return [r.data() for r in result]

    def get_precedents_for_concepts(self, legal_concepts: List[str], jurisdiction: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top precedents tied to any of the specified concepts."""
        if not self.driver:
            return []

        query = """
        MATCH (lc:LegalConcept)
        WHERE lc.concept_id IN $concepts
        MATCH (c:Case)-[rel:INVOLVES_CONCEPT]->(lc)
        WHERE c.precedent_value > 0.6 AND ($jurisdiction IS NULL OR c.jurisdiction = $jurisdiction)
        OPTIONAL MATCH (c)-[:DECIDED_BY]->(court:Court)
        RETURN c.case_id AS case_id,
               c.title AS title,
               c.outcome AS outcome,
               c.precedent_value AS precedent_value,
               court.name AS court_name,
               rel.relevance_score AS relevance_score
        ORDER BY precedent_value DESC, relevance_score DESC
        LIMIT $limit
        """

        with self._session() as session:
            result = session.run(
                query,
                {"concepts": legal_concepts or [], "jurisdiction": jurisdiction, "limit": limit},
            )
            return [r.data() for r in result]

    def predict_outcome_from_graph(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Simple outcome aggregation using similar cases as weak prior."""
        similar = self.find_similar_cases(
            legal_area=features.get("legal_area", ""),
            procedure_type=features.get("procedure_type"),
            legal_concepts=features.get("legal_concepts", []),
            court_id=features.get("court_id"),
            limit=25,
        )
        if not similar:
            return None

        # Aggregate probabilities by outcome proportional to similarity
        buckets: Dict[str, float] = {}
        count: Dict[str, int] = {}
        for row in similar:
            outcome = (row.get("outcome") or "unknown").lower()
            sim = float(row.get("similarity") or 0)
            buckets[outcome] = buckets.get(outcome, 0.0) + max(sim, 0.0)
            count[outcome] = count.get(outcome, 0) + 1

        total = sum(buckets.values()) or 1.0
        ranked = sorted(
            (
                {"outcome": k, "probability": v / total, "support": count.get(k, 0)}
                for k, v in buckets.items()
            ),
            key=lambda x: x["probability"],
            reverse=True,
        )
        top = ranked[0]
        return {"predicted_outcome": top["outcome"], "confidence": top["probability"], "details": ranked}

    # ------------------------
    # Hybrid semantic + graph search for similar cases
    # ------------------------
    def search_similar_cases_hybrid(
        self,
        query_text: str,
        top_k: int = 20,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """Vector search in Neo4j + re-rank using graph authority signals.

        Returns list of dicts: {case_id, title, court_id, jurisdiction, vector_score, graph_score, final_score}
        """
        if not self.driver:
            return []

        # Defaults: blend vector and graph signals
        w = {
            "vector": 0.6,
            "precedent": 0.2,
            "court": 0.15,
            "recency": 0.05,
        }
        if weights:
            w.update(weights)

        # Embed the query text using Mistral directly if available
        try:
            from mistralai import Mistral  # type: ignore
            from config.settings import MISTRAL_API_KEY as MISTRAL_KEY  # type: ignore
            client = Mistral(api_key=MISTRAL_KEY)
            vec = client.embeddings.create(model="mistral-embed", inputs=[query_text]).data[0].embedding
        except Exception:
            vec = []

        with self._session() as session:
            # If no vector, fallback to fulltext ranking on summary/title
            if not vec:
                base = session.run(
                    """
                    CALL db.index.fulltext.queryNodes('case_content_text', $q) YIELD node, score
                    RETURN node.case_id as case_id, node.title as title, coalesce(node.court_id,'') as court_id,
                           coalesce(node.jurisdiction,'') as jurisdiction, score as vector_score
                    ORDER BY score DESC LIMIT $k
                    """,
                    {"q": query_text, "k": top_k},
                )
            else:
                base = session.run(
                    """
                    CALL db.index.vector.queryNodes('case_embeddings', $vec, $k) YIELD node, score
                    RETURN node.case_id as case_id, node.title as title, coalesce(node.court_id,'') as court_id,
                           coalesce(node.jurisdiction,'') as jurisdiction, score as vector_score
                    """,
                    {"vec": vec, "k": top_k},
                )

            base_rows = [r.data() for r in base]
            if not base_rows:
                return []

            ids = [row["case_id"] for row in base_rows]
            # Compute simple graph features for these ids
            gf = session.run(
                """
                UNWIND $ids as cid
                MATCH (c:Case {case_id: cid})
                OPTIONAL MATCH (c)-[hp:HAS_PRECEDENT]->(p:Case)
                WITH c, sum(coalesce(hp.precedent_weight,0.5)) as precedent_strength
                OPTIONAL MATCH (c)-[:HEARD_IN]->(ct:Court)
                WITH c, precedent_strength, ct.level as court_level
                WITH c, precedent_strength,
                     CASE court_level WHEN 'supreme' THEN 1.0 WHEN 'superior' THEN 0.7 ELSE 0.5 END as court_score
                WITH c, precedent_strength, court_score,
                     (CASE WHEN c.resolution_date IS NOT NULL THEN (1.0 / (1 + duration.inDays(c.resolution_date, date()).days)) ELSE 0.2 END) as recency
                RETURN c.case_id as case_id, precedent_strength, court_score, recency
                """,
                {"ids": ids},
            )
            gmap = {r["case_id"]: r.data() if hasattr(r, 'data') else r for r in gf}

            # Merge and score
            out: List[Dict[str, Any]] = []
            for row in base_rows:
                gi = gmap.get(row["case_id"], {})
                precedent = float(gi.get("precedent_strength", 0.0))
                court_score = float(gi.get("court_score", 0.5))
                recency = float(gi.get("recency", 0.2))
                vector_score = float(row.get("vector_score", 0.0))
                final = (
                    w["vector"] * vector_score
                    + w["precedent"] * precedent
                    + w["court"] * court_score
                    + w["recency"] * recency
                )
                out.append({
                    **row,
                    "graph_score": {
                        "precedent": precedent,
                        "court": court_score,
                        "recency": recency,
                    },
                    "final_score": final,
                })

            out.sort(key=lambda x: x["final_score"], reverse=True)
            return out[:top_k]


