// Neo4j Data - Solo operaciones de datos (DML)
// Ejecutar este archivo después del esquema

// Create Case node
MERGE (c:Case {process_number: 'T-2266809'})
SET c.case_id = 'T-2266809',
    c.process_type = 'ACCIÓN DE TUTELA',
    c.provision_type = 'SENTENCIA',
    c.sentence_number = 'T-629-2009',
    c.provision_date = date('2009-09-04'),
    c.court = 'CORTE CONSTITUCIONAL',
    c.section = 'SALA CUARTA DE REVISIÓN',
    c.reporting_judge = 'GABRIEL EDUARDO MENDOZA MARTELO',
    c.plaintiff = 'ADOLDO RAAD HERNÁNDEZ',
    c.defendant = 'PROCURADURÍA GENERAL DE LA NACIÓN',
    c.ruling_direction = 'FAVORABLE',
    c.relevant_facts = 'La Procuraduría General de la Nación, declaró disciplinariamente responsable al Presidente del Concejo Distrital de Cartagena Adolfo Raad Hernández, imponiendo como sanción la destitución del cargo e inhabilidad para el ejercicio de función pública por veinte (20) años.',
    c.legal_problem = '¿Es procedente la acción de tutela para declarar la suspensión de los efectos de una sanción de destitución e inhabilidad general interpuesta por parte de la Procuraduría General de la Nación al Presidente del Concejo de Cartagena?',
    c.challenged_act = 'N/A',
    c.legal_foundation_demand = 'N/A',
    c.legal_foundation_defense = 'N/A',
    c.supporting_normativity = ['Artículo 86 de la Constitución Política', 'Artículo 6º numeral 1° del Decreto 2591 de 1991'],
    c.supporting_jurisprudence = ['T-161 de 2009', 'T-640 de 1996', 'T-106 de 1993'],
    c.legal_thesis = 'Según la jurisprudencia de la Corte Constitucional, la acción de tutela no es procedente para declarar la suspensión de los efectos de las decisiones adoptadas en materia sancionatoria por la Procuraduría General de la Nación',
    c.extract = 'Como ya se expuso, en desarrollo del principio de subsidiariedad, la jurisprudencia constitucional ha señalado que en los casos en que el accionante tenga a su alcance otros medios o recursos de defensa judicial',
    c.dissenting_vote = 'N/A',
    c.dissenting_thesis = 'N/A',
    c.dissenting_extract = 'N/A',
    c.clarifying_vote = 'N/A',
    c.clarifying_thesis = 'N/A',
    c.clarifying_extract = 'N/A',
    c.similarity_vector = [0.1, 0.2, 0.3],
    c.created_at = datetime(),
    c.updated_at = datetime();

// Create Party nodes
MERGE (p1:Party {name: 'ADOLDO RAAD HERNÁNDEZ'})
SET p1.party_id = 'party_1',
    p1.party_type = 'PLAINTIFF',
    p1.role = 'Presidente del Concejo Distrital de Cartagena',
    p1.created_at = datetime();

MERGE (p2:Party {name: 'PROCURADURÍA GENERAL DE LA NACIÓN'})
SET p2.party_id = 'party_2',
    p2.party_type = 'DEFENDANT',
    p2.role = 'Administrative Entity',
    p2.created_at = datetime();

// Create Court node
MERGE (co:Court {name: 'CORTE CONSTITUCIONAL'})
SET co.court_id = 'court_1',
    co.section = 'SALA CUARTA DE REVISIÓN',
    co.jurisdiction = 'Constitutional',
    co.created_at = datetime();

// Create Judge node
MERGE (j:Judge {name: 'GABRIEL EDUARDO MENDOZA MARTELO'})
SET j.judge_id = 'judge_1',
    j.court = 'CORTE CONSTITUCIONAL',
    j.section = 'SALA CUARTA DE REVISIÓN',
    j.role = 'REPORTING_JUDGE',
    j.created_at = datetime();

// Create LegalConcept nodes
MERGE (lc1:LegalConcept {concept: 'ACCIÓN DE TUTELA'})
SET lc1.concept_id = 'concept_1',
    lc1.category = 'Constitutional Remedy',
    lc1.description = 'Mecanismo de protección de derechos fundamentales',
    lc1.created_at = datetime();

MERGE (lc2:LegalConcept {concept: 'DEBIDO PROCESO'})
SET lc2.concept_id = 'concept_2',
    lc2.category = 'Fundamental Right',
    lc2.description = 'Garantía constitucional de proceso justo y equitativo',
    lc2.created_at = datetime();

// Create LegalProblem node
MERGE (lp:LegalProblem {problem_id: 'problem_1'})
SET lp.problem_text = '¿Es procedente la acción de tutela para declarar la suspensión de los efectos de una sanción de destitución e inhabilidad general interpuesta por parte de la Procuraduría General de la Nación al Presidente del Concejo de Cartagena?',
    lp.problem_type = 'Procedural',
    lp.legal_area = 'Constitutional Law',
    lp.complexity_level = 'High',
    lp.created_at = datetime();

// Create LegalThesis node
MERGE (lt:LegalThesis {thesis_id: 'thesis_1'})
SET lt.thesis_text = 'Según la jurisprudencia de la Corte Constitucional, la acción de tutela no es procedente para declarar la suspensión de los efectos de las decisiones adoptadas en materia sancionatoria por la Procuraduría General de la Nación',
    lt.thesis_type = 'Doctrinal',
    lt.legal_area = 'Constitutional Law',
    lt.precedent_value = 0.9,
    lt.created_at = datetime();

// Create LegalNorm nodes
MERGE (ln1:LegalNorm {norm_id: 'norm_1'})
SET ln1.norm_text = 'Artículo 86 de la Constitución Política',
    ln1.norm_type = 'Constitutional',
    ln1.legal_area = 'Constitutional Law',
    ln1.created_at = datetime();

MERGE (ln2:LegalNorm {norm_id: 'norm_2'})
SET ln2.norm_text = 'Artículo 6º numeral 1° del Decreto 2591 de 1991',
    ln2.norm_type = 'Regulatory',
    ln2.legal_area = 'Constitutional Law',
    ln2.created_at = datetime();

// Create relationships
MATCH (c:Case {process_number: 'T-2266809'})
MATCH (p1:Party {name: 'ADOLDO RAAD HERNÁNDEZ'})
MATCH (p2:Party {name: 'PROCURADURÍA GENERAL DE LA NACIÓN'})
MATCH (co:Court {name: 'CORTE CONSTITUCIONAL'})
MATCH (j:Judge {name: 'GABRIEL EDUARDO MENDOZA MARTELO'})
MATCH (lp:LegalProblem {problem_id: 'problem_1'})
MATCH (lt:LegalThesis {thesis_id: 'thesis_1'})
MATCH (lc1:LegalConcept {concept: 'ACCIÓN DE TUTELA'})
MATCH (lc2:LegalConcept {concept: 'DEBIDO PROCESO'})
MATCH (ln1:LegalNorm {norm_id: 'norm_1'})
MATCH (ln2:LegalNorm {norm_id: 'norm_2'})

MERGE (c)-[:HAS_PLAINTIFF]->(p1)
MERGE (c)-[:HAS_DEFENDANT]->(p2)
MERGE (c)-[:HEARD_BY]->(co)
MERGE (c)-[:REPORTED_BY]->(j)
MERGE (c)-[:ADDRESSES_PROBLEM]->(lp)
MERGE (c)-[:ESTABLISHES_THESIS]->(lt)

MERGE (c)-[:INVOLVES_CONCEPT]->(lc1)
MERGE (c)-[:INVOLVES_CONCEPT]->(lc2)

MERGE (c)-[:CITES_NORM]->(ln1)
MERGE (c)-[:CITES_NORM]->(ln2)

MERGE (c)-[:CITES_CASE {case_number: 'T-161 de 2009'}]->(c)
MERGE (c)-[:CITES_CASE {case_number: 'T-640 de 1996'}]->(c)
MERGE (c)-[:CITES_CASE {case_number: 'T-106 de 1993'}]->(c);
