"""
Neo4j HTTP API Client for Aura
Uses the HTTP Query API instead of Bolt protocol
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Neo4jQueryResult:
    """Result from Neo4j HTTP query"""
    data: List[Dict[str, Any]]
    columns: List[str]
    success: bool
    error: Optional[str] = None

class Neo4jHTTPClient:
    """HTTP-based Neo4j client for Aura with Bolt fallback"""
    
    def __init__(self, 
                 http_url: str = None,
                 username: str = None, 
                 password: str = None,
                 database: str = "neo4j"):
        # Separate authentication and query endpoints
        self.base_url = "https://c8a93607.databases.neo4j.io"
        self.auth_url = f"{self.base_url}/db/neo4j/tx/commit"  # Authentication endpoint
        self.query_url = http_url or f"{self.base_url}/db/neo4j/query/v2"  # Query endpoint
        self.username = username
        self.password = password
        self.database = database
        self.session = requests.Session()
        self.use_bolt_fallback = True  # Use Bolt as fallback
        self.auth_token = None
        
        # Set up authentication
        if self.username and self.password:
            self._authenticate()
            logger.info("Neo4j HTTP client initialized with authentication")
        else:
            logger.warning("Neo4j HTTP client initialized without authentication")
        
        # Try to initialize Bolt fallback
        self.bolt_driver = None
        if self.use_bolt_fallback:
            try:
                from neo4j import GraphDatabase
                bolt_uri = f"neo4j+s://c8a93607.databases.neo4j.io"
                self.bolt_driver = GraphDatabase.driver(bolt_uri, auth=(self.username, self.password))
                logger.info("Neo4j Bolt fallback driver initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Bolt fallback: {e}")
                self.bolt_driver = None
    
    def _authenticate(self):
        """Authenticate with Neo4j Aura and get token"""
        try:
            # First, try to authenticate using basic auth with a simple query
            auth_payload = {
                "statements": [{
                    "statement": "RETURN 1 as test",
                    "parameters": {},
                    "resultDataContents": ["row"],
                    "includeStats": False
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Use basic auth for initial authentication
            response = requests.post(
                self.auth_url,
                json=auth_payload,
                headers=headers,
                auth=(self.username, self.password),
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Neo4j authentication successful")
                # Store the session for future requests
                self.session.auth = (self.username, self.password)
                return True
            else:
                logger.warning(f"Neo4j authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.warning(f"Neo4j authentication error: {e}")
            return False
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Neo4jQueryResult:
        """Execute a Cypher query via HTTP API with Bolt fallback"""
        # Try HTTP first, then fallback to Bolt
        if not self._try_http_query(query, parameters):
            return self._try_bolt_query(query, parameters)
        return self._last_result
    
    def _try_http_query(self, query: str, parameters: Dict[str, Any] = None) -> bool:
        """Try to execute query via HTTP API"""
        try:
            # Use the query endpoint for actual queries
            payload = {
                "query": query,
                "parameters": parameters or {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = self.session.post(
                self.query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Parse Neo4j Aura Query API response format
                if "results" in result_data and len(result_data["results"]) > 0:
                    result = result_data["results"][0]
                    if "data" in result and len(result["data"]) > 0:
                        # Extract row data
                        rows = []
                        columns = result.get("columns", [])
                        for row in result["data"]:
                            if "row" in row:
                                rows.append(dict(zip(columns, row["row"])))
                        
                        self._last_result = Neo4jQueryResult(
                            data=rows,
                            columns=columns,
                            success=True
                        )
                        return True
                    else:
                        self._last_result = Neo4jQueryResult(
                            data=[],
                            columns=result.get("columns", []),
                            success=True
                        )
                        return True
                else:
                    # Handle direct response format (not wrapped in results)
                    if "data" in result_data and len(result_data["data"]) > 0:
                        rows = []
                        columns = result_data.get("columns", [])
                        for row in result_data["data"]:
                            if "row" in row:
                                rows.append(dict(zip(columns, row["row"])))
                        
                        self._last_result = Neo4jQueryResult(
                            data=rows,
                            columns=columns,
                            success=True
                        )
                        return True
                    else:
                        self._last_result = Neo4jQueryResult(
                            data=[],
                            columns=result_data.get("columns", []),
                            success=True
                        )
                        return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.warning(f"Neo4j HTTP query failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.warning(f"Neo4j HTTP query error: {e}")
            return False
    
    def _try_bolt_query(self, query: str, parameters: Dict[str, Any] = None) -> Neo4jQueryResult:
        """Try to execute query via Bolt protocol"""
        if not self.bolt_driver:
            logger.warning("Bolt driver not available, returning empty result")
            return Neo4jQueryResult(
                data=[],
                columns=[],
                success=False,
                error="No Bolt driver available"
            )
        
        try:
            with self.bolt_driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                data = []
                columns = result.keys()
                
                for record in result:
                    data.append(dict(record))
                
                return Neo4jQueryResult(
                    data=data,
                    columns=list(columns),
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Neo4j Bolt query error: {e}")
            return Neo4jQueryResult(
                data=[],
                columns=[],
                success=False,
                error=str(e)
            )
    
    def find_similar_cases(self, 
                          legal_concepts: List[str], 
                          legal_area: str = None,
                          procedure_type: str = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar cases based on legal concepts"""
        try:
            # Create a query to find cases with similar concepts
            concepts_str = "|".join(legal_concepts)
            query = """
            MATCH (c:Case)-[:HAS_CONCEPT]->(concept:Concept)
            WHERE concept.name =~ $concept_pattern
            RETURN c.title as title, 
                   c.court as court, 
                   c.date as date,
                   c.summary as summary,
                   c.url as url,
                   collect(concept.name) as concepts
            ORDER BY size(concepts) DESC
            LIMIT $limit
            """
            
            result = self.execute_query(query, {
                "concept_pattern": f"(?i).*({concepts_str}).*",
                "limit": limit
            })
            
            if result.success:
                return result.data
            else:
                logger.warning(f"Failed to find similar cases: {result.error}")
                return []
                
        except Exception as e:
            logger.error(f"Error finding similar cases: {e}")
            return []
    
    def get_precedents_for_concepts(self, 
                                   legal_concepts: List[str],
                                   jurisdiction: str = "Colombia",
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Get precedents for specific legal concepts"""
        try:
            concepts_str = "|".join(legal_concepts)
            query = """
            MATCH (p:Precedent)-[:RELATES_TO]->(concept:Concept)
            WHERE concept.name =~ $concept_pattern
            AND p.jurisdiction = $jurisdiction
            RETURN p.title as title,
                   p.court as court,
                   p.date as date,
                   p.summary as summary,
                   p.url as url,
                   p.impact as impact,
                   collect(concept.name) as concepts
            ORDER BY p.date DESC
            LIMIT $limit
            """
            
            result = self.execute_query(query, {
                "concept_pattern": f"(?i).*({concepts_str}).*",
                "jurisdiction": jurisdiction,
                "limit": limit
            })
            
            if result.success:
                return result.data
            else:
                logger.warning(f"Failed to get precedents: {result.error}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting precedents: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test the Neo4j HTTP connection"""
        try:
            query = "RETURN 1 as test"
            result = self.execute_query(query)
            return result.success
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False

# Global client instance
_neo4j_client = None

def get_neo4j_http_client() -> Neo4jHTTPClient:
    """Get or create the global Neo4j HTTP client"""
    global _neo4j_client
    
    if _neo4j_client is None:
        import os
        _neo4j_client = Neo4jHTTPClient(
            http_url=os.getenv("NEO4J_HTTP_URL"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )
    
    return _neo4j_client
