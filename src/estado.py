"""
State Management for RFM-LDE Multiagent

Manages conversation state, group definitions, and results persistence
across multi-turn interactions with the commercial team.

Classes:
    - GrupoDefinicion: Cluster + quintile + product segment definition
    - Periodo: Time range (relative or absolute)
    - EstadoGrafo: Complete conversation state for LangGraph
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TipoPeriodo(str, Enum):
    """Time period types for queries"""
    RELATIVE = "relative"
    ABSOLUTE = "absolute"


class Periodo(BaseModel):
    """
    Time range definition for queries.

    Attributes:
        type: Either 'relative' (e.g., "last_week") or 'absolute' (e.g., "2026-11-01:2026-11-06")
        value: String representation of the period
    """
    type: TipoPeriodo = TipoPeriodo.RELATIVE
    value: str = "last_week"

    def __str__(self) -> str:
        """Human-readable period representation"""
        if self.type == TipoPeriodo.RELATIVE:
            return f"Last {self.value.replace('_', ' ')}"
        return f"{self.value}"


class GrupoDefinicion(BaseModel):
    """
    Defines the cluster/quintile group for analysis.

    Attributes:
        cluster: 0-3 (K-Means clusters) or None for all
        quintil: 1-5 (LightGBM quintiles) or None for all
        run_date: YYYY-MM-DD of latest segmentation run
        subgrupo_producto: Optional product segment (AADD, Gaming, Sports, etc.)
    """
    cluster: Optional[int] = Field(None, ge=0, le=3, description="Cluster 0-3")
    quintil: Optional[int] = Field(None, ge=1, le=5, description="Quintile 1-5")
    run_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    subgrupo_producto: Optional[str] = None

    def __str__(self) -> str:
        """Human-readable group description"""
        parts = []
        if self.cluster is not None:
            parts.append(f"Cluster {self.cluster}")
        if self.quintil is not None:
            parts.append(f"Quintile {self.quintil}")
        if self.subgrupo_producto:
            parts.append(f"({self.subgrupo_producto})")
        return " ".join(parts) if parts else "All players"


@dataclass
class ArtefactoExportacion:
    """
    Exported data artifact (CSV, JSON, or chart).

    Attributes:
        tipo: 'csv', 'json', 'chart_svg'
        contenido: Raw data or SVG string
        fecha_generacion: When artifact was created
        tamano_bytes: Size of exported data
    """
    tipo: str
    contenido: str
    fecha_generacion: str = field(default_factory=lambda: datetime.now().isoformat())
    tamano_bytes: int = 0


@dataclass
class EstadoGrafo:
    """
    Complete state for LangGraph agent interactions.

    Persists across turns to maintain context, cluster selection, and results.
    Designed for stateless Lambda deployment (client sends full state each turn).

    Attributes:
        mensajes: Conversation history
        grupo: Cluster/quintile definition (persists across turns)
        periodo: Time range (updated per turn if user specifies)
        resultados: Specialist outputs (cleared at turn start, populated during execution)
        pasos: Step counter (max 8 before force-respond to prevent loops)
        archivo: Exported CSV/JSON if user requested export
        aclaracion: Question for user if group/quintile ambiguous
    """
    mensajes: List[Dict[str, Any]] = field(default_factory=list)
    grupo: GrupoDefinicion = field(default_factory=GrupoDefinicion)
    periodo: Periodo = field(default_factory=Periodo)
    resultados: Dict[str, Any] = field(default_factory=dict)
    pasos: int = 0
    archivo: Optional[ArtefactoExportacion] = None
    aclaracion: Optional[str] = None

    def reset_resultados(self) -> None:
        """Clear specialist results at turn start (idempotent)"""
        self.resultados = {}
        self.pasos = 0

    def increment_pasos(self) -> int:
        """Increment step counter and return new value"""
        self.pasos += 1
        return self.pasos

    def debe_responder(self) -> bool:
        """True if step counter >= max (force response to avoid loops)"""
        return self.pasos >= 8

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict"""
        return {
            "grupo": self.grupo.model_dump(),
            "periodo": self.periodo.model_dump(),
            "pasos": self.pasos,
            "archivo": {
                "tipo": self.archivo.tipo,
                "tamano_bytes": self.archivo.tamano_bytes,
            } if self.archivo else None,
            "aclaracion": self.aclaracion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EstadoGrafo":
        """Deserialize from JSON dict"""
        estado = cls()
        if "grupo" in data:
            estado.grupo = GrupoDefinicion(**data["grupo"])
        if "periodo" in data:
            estado.periodo = Periodo(**data["periodo"])
        if "pasos" in data:
            estado.pasos = data["pasos"]
        if "aclaracion" in data:
            estado.aclaracion = data["aclaracion"]
        return estado
