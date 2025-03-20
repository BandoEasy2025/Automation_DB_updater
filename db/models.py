from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4

class Grant(BaseModel):
    """Model representing a grant (bando) in the Supabase database"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    record_id: Optional[str] = None
    nome_bando: str
    promotore: str
    descrizione_breve: Optional[str] = None
    descrizione_bando: Optional[str] = None
    a_chi_si_rivolge: Optional[str] = None
    settore: Optional[str] = None
    codice_ateco: Optional[str] = None
    sezione: Optional[str] = None
    cumulabilita: Optional[bool] = None
    spese_ammissibili: Optional[str] = None
    spese_ammissibili_f: Optional[str] = None
    richiesta_massima: Optional[float] = None
    richiesta_minima: Optional[float] = None
    dotazione: Optional[float] = None
    percentuale_fondo_perduto: Optional[float] = None
    descrizione_fondo_perduto: Optional[str] = None
    data_apertura: Optional[datetime] = None
    scadenza: Optional[datetime] = None
    scadenza_interna: Optional[datetime] = None
    link_bando: Optional[str] = None
    link_sito_bando: Optional[str] = None
    iter_presentazione_domanda: Optional[str] = None
    descrizione_tipo_agevolazione_emanazione: Optional[str] = None
    esempi_progetti_ammissibili: Optional[str] = None
    regime: Optional[str] = None
    documentazione_necessaria: Optional[str] = None
    tipo: Optional[str] = None
    emanazione: Optional[str] = None
    stato: Optional[str] = None
    visualizzazione: Optional[int] = 0
    data_creazione: Optional[datetime] = Field(default_factory=datetime.now)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    update_in_db: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for Supabase insertion"""
        data = self.dict(exclude_none=True)
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Grant":
        """Create model from database dictionary"""
        return cls(**data)


class Attachment(BaseModel):
    """Base model for attachments (allegati)"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    bando_id: UUID
    numero: Optional[int] = None
    nome: str
    link_originale: Optional[str] = None
    file_path: Optional[str] = None
    file_name: str
    mime_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for Supabase insertion"""
        data = self.dict(exclude_none=True)
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        if "bando_id" in data and isinstance(data["bando_id"], UUID):
            data["bando_id"] = str(data["bando_id"])
        return data


class InformativeAttachment(Attachment):
    """Model for informative attachments"""
    pass


class CompilativeAttachment(Attachment):
    """Model for compilative attachments"""
    pass


class StatusLog(BaseModel):
    """Model for status change logs in bandi_status_log table"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    bando_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for Supabase insertion"""
        data = self.dict(exclude_none=True)
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        if "bando_id" in data and isinstance(data["bando_id"], UUID):
            data["bando_id"] = str(data["bando_id"])
        return data


class RawGrantData(BaseModel):
    """Model for raw data scraped from websites before processing"""
    title: str
    promoter: str
    description: Optional[str] = None
    eligibility: Optional[str] = None
    sector: Optional[str] = None
    ateco_code: Optional[str] = None
    eligible_expenses: Optional[str] = None
    max_request: Optional[str] = None
    min_request: Optional[str] = None
    total_funding: Optional[str] = None
    grant_percentage: Optional[str] = None
    opening_date: Optional[str] = None
    closing_date: Optional[str] = None
    url: str
    website_url: Optional[str] = None
    application_process: Optional[str] = None
    required_documentation: Optional[str] = None
    type: Optional[str] = None
    source: Optional[str] = None
    source_url: str
    informative_attachments: List[Dict[str, str]] = Field(default_factory=list)
    compilative_attachments: List[Dict[str, str]] = Field(default_factory=list)