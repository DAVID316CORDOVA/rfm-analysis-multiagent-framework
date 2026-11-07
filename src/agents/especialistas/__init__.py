"""
Specialist Agents for RFM-LDE Multiagent

Each specialist agent handles a single domain:
- AADD: Sports betting analysis
- Bonos: Bonus tracking and analysis
- Depositos/Retiros: Financial flow analysis
- Ventas/GGW: Revenue and gaming win analysis
- Exportar: Data export and filtering
- Grafico: Visualization generation
- Metodologia: Model quality and training details
"""

from typing import Any, Dict

# Specialist imports would go here
# from .aadd import AaddSpecialist
# from .bonos import BonosSpecialist
# etc.

__all__ = [
    "aadd",
    "bonos",
    "depositos_retiros",
    "exportar",
    "grafico",
    "metodologia",
    "ventas_ggw",
]
