class ColombianLegalFramework:
    CASE_TYPES = {
        "proceso_laboral": "Proceso Laboral",
        "proceso_civil": "Proceso Civil",
        "proceso_penal": "Proceso Penal",
        "proceso_administrativo": "Proceso Administrativo",
        "proceso_comercial": "Proceso Comercial"
    }

    ADMINISTRATIVE_PROCEDURES = {
        "conciliacion": "Conciliación",
        "recurso_reposicion": "Recurso de Reposición",
        "recurso_apelacion": "Recurso de Apelación",
        "tutela": "Acción de Tutela",
        "derecho_peticion": "Derecho de Petición",
        "proceso_ejecutivo": "Proceso Ejecutivo",
        "proceso_ordinario": "Proceso Ordinario",
        "proceso_verbal": "Proceso Verbal",
        "proceso_abreviado": "Proceso Abreviado",
        "ninguno": "Ninguno"
    }

    JURISDICTIONS = {
        "ordinaria": "Jurisdicción Ordinaria",
        "administrativa": "Jurisdicción Administrativa",
        "constitucional": "Jurisdicción Constitucional",
        "especial": "Jurisdicción Especial"
    }

    LEGAL_AREAS = {
        "laboral": "Derecho Laboral",
        "civil": "Derecho Civil",
        "penal": "Derecho Penal",
        "administrativo": "Derecho Administrativo",
        "comercial": "Derecho Comercial",
        "constitucional": "Derecho Constitucional",
        "familia": "Derecho de Familia"
    }

    @classmethod
    def get_case_type_name(cls, case_type: str) -> str:
        return cls.CASE_TYPES.get(case_type, "Desconocido")

    @classmethod
    def get_administrative_procedure_name(cls, procedure: str) -> str:
        return cls.ADMINISTRATIVE_PROCEDURES.get(procedure, "Desconocido")

    @classmethod
    def get_jurisdiction_name(cls, jurisdiction: str) -> str:
        return cls.JURISDICTIONS.get(jurisdiction, "Desconocido")

    @classmethod
    def get_legal_area_name(cls, area: str) -> str:
        return cls.LEGAL_AREAS.get(area, "Desconocido")

    @classmethod
    def validate_case_type(cls, case_type: str) -> bool:
        return case_type in cls.CASE_TYPES

    @classmethod
    def validate_administrative_procedure(cls, procedure: str) -> bool:
        return procedure in cls.ADMINISTRATIVE_PROCEDURES

    @classmethod
    def validate_jurisdiction(cls, jurisdiction: str) -> bool:
        return jurisdiction in cls.JURISDICTIONS

    @classmethod
    def validate_legal_area(cls, area: str) -> bool:
        return area in cls.LEGAL_AREAS 