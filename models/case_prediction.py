from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class CasePredictionRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "case_type": "proceso_laboral",
                "jurisdiction": "Colombia",
                "key_facts": ["Despido sin justa causa", "Empleado con 5 años de antigüedad"],
                "legal_issues": ["Indemnización por despido", "Pago de prestaciones"],
                "judge_name": None,
                "opposing_counsel": None,
                "relevant_precedents": None,
                "administrative_procedure": None,
                "legal_terms": None
            }
        }
    )

    case_type: str = Field(..., description="Tipo de proceso")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    key_facts: List[str] = Field(..., description="Hechos relevantes")
    legal_issues: List[str] = Field(..., description="Problemas jurídicos")
    judge_name: Optional[str] = Field(None, description="Nombre del juez")
    opposing_counsel: Optional[str] = Field(None, description="Contraparte")
    relevant_precedents: Optional[List[str]] = Field(None, description="Precedentes relevantes")
    administrative_procedure: Optional[str] = Field(None, description="Procedimiento administrativo")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos") 