"""
Bonuses Specialist Agent

Handles all queries related to bonus tracking and analysis:
- Bonuses assigned to players
- Bonuses activated/used
- Bonuses won (player profit from bonus)
- Bonus activation rates
- Bonus ROI analysis

Data source: Athena dwh_raw_pe.bonos_asignados_convertidos
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BonoQuery:
    """Query parameters for bonus analysis"""
    cluster: int
    quintil: int
    fecha_inicio: str
    fecha_fin: str
    estado: Optional[str] = None  # asignado, activado, ganado


class BonosSpecialist:
    """
    Specialist agent for bonus analysis.

    Answers questions about:
    - Total bonuses assigned/activated/won
    - Activation rates by cluster
    - Player engagement with bonuses
    - Bonus profitability
    """

    def __init__(self, athena_client: Any = None):
        """
        Initialize bonuses specialist.

        Args:
            athena_client: Boto3 Athena client
        """
        self.athena_client = athena_client
        self.logger = logger

    async def consultar_bonos(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str],
        estado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query bonus data for cluster/quintile.

        Args:
            cluster: Cluster ID (0-3)
            quintil: Quintile ID (1-5)
            periodo: Time period {"type": "relative"|"absolute", "value": "..."}
            estado: Filter by state (asignado, activado, ganado)

        Returns:
            Dictionary with bonus statistics
        """
        try:
            # In production: parse periodo and build actual SQL query
            fecha_inicio = "2026-10-01"
            fecha_fin = "2026-11-06"

            # Build SQL query
            query = f"""
            SELECT
                COUNT(*) as total_bonos_asignados,
                SUM(CASE WHEN estado='activado' THEN 1 ELSE 0 END) as total_activados,
                SUM(CASE WHEN estado='ganado' THEN 1 ELSE 0 END) as total_ganados,
                COUNT(DISTINCT player_id) as num_jugadores_unicos,
                AVG(monto_bono) as monto_promedio,
                SUM(ganancia_neta) as ganancia_total,
                ROUND(100.0 * SUM(CASE WHEN estado='activado' THEN 1 ELSE 0 END) / COUNT(*), 2) as tasa_activacion
            FROM "dwh_raw_pe"."bonos_asignados_convertidos"
            WHERE cluster = {cluster}
              AND quintil = {quintil}
              AND fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
              {f"AND estado = '{estado}'" if estado else ""}
            """

            self.logger.info(f"Bonus query: cluster={cluster}, quintil={quintil}")

            # Execute query (mocked in dev)
            results = {
                "total_bonos_asignados": 2847,
                "total_activados": 1923,
                "total_ganados": 856,
                "num_jugadores_unicos": 342,
                "monto_promedio": 150.00,
                "ganancia_total": 38420.50,
                "tasa_activacion": 67.5,
                "activacion_por_dia": [
                    {"fecha": "2026-11-06", "activados": 245, "tasa": "68%"},
                    {"fecha": "2026-11-05", "activados": 189, "tasa": "65%"},
                    {"fecha": "2026-11-04", "activados": 267, "tasa": "72%"},
                ]
            }

            return results

        except Exception as e:
            self.logger.error(f"Error in consultar_bonos: {str(e)}")
            return {"error": str(e), "total_bonos_asignados": 0}

    async def bonos_top_tipos(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get top bonus types by activation rate.

        Shows which bonus types are most popular with this cluster.

        Args:
            cluster: Cluster ID
            quintil: Quintile ID
            periodo: Time period
            limit: Number of top bonuses to return

        Returns:
            List of bonus types with stats
        """
        try:
            results = {
                "top_bonuses": [
                    {
                        "tipo_bono": "Bono de Bienvenida",
                        "num_jugadores": 289,
                        "activacion_rate": "78%",
                        "ganancia_promedio": 125.50,
                    },
                    {
                        "tipo_bono": "Reload 50%",
                        "num_jugadores": 156,
                        "activacion_rate": "65%",
                        "ganancia_promedio": 89.75,
                    },
                    {
                        "tipo_bono": "Free Spins x100",
                        "num_jugadores": 98,
                        "activacion_rate": "52%",
                        "ganancia_promedio": -45.20,
                    },
                ]
            }

            self.logger.info(f"Top bonuses: {len(results['top_bonuses'])} types")
            return results

        except Exception as e:
            self.logger.error(f"Error in bonos_top_tipos: {str(e)}")
            return {"error": str(e)}

    async def bono_roi_analisis(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze bonus ROI (Return On Investment) for the house.

        Answers: Does this cluster generate profit or loss from bonuses?

        Args:
            cluster: Cluster ID
            quintil: Quintile ID
            periodo: Time period

        Returns:
            ROI metrics and analysis
        """
        try:
            results = {
                "roi_bono": {
                    "total_bonos_otorgados": 2847,
                    "monto_total_bonos": 427050.00,
                    "ganancia_neta": 38420.50,
                    "roi_porcentaje": 9.0,
                    "interpretacion": "Positivo - el cluster genera ganancia",
                    "jugadores_ganadores": 856,
                    "jugadores_perdedores": 245,
                    "ratio_win_loss": 3.5,
                },
                "comparacion_clusters": [
                    {"cluster": "C0 (New)", "roi": "12%", "estado": "Alto"},
                    {"cluster": "C1 (Dormant)", "roi": "5%", "estado": "Medio"},
                    {"cluster": "C2 (Active)", "roi": "8%", "estado": "Medio"},
                    {"cluster": "C3 (High Value)", "roi": "15%", "estado": "Alto"},
                ]
            }

            self.logger.info(f"ROI analysis: {results['roi_bono']['roi_porcentaje']}%")
            return results

        except Exception as e:
            self.logger.error(f"Error in bono_roi_analisis: {str(e)}")
            return {"error": str(e)}

    async def bono_duracion_media(
        self,
        cluster: int,
        quintil: int,
        periodo: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate average time from assignment to activation.

        Shows how quickly this cluster engages with bonuses.

        Args:
            cluster: Cluster ID
            quintil: Quintile ID
            periodo: Time period

        Returns:
            Duration statistics
        """
        try:
            results = {
                "duracion_promedio_horas": 3.5,
                "duracion_mediana_horas": 2.1,
                "rango": {
                    "min_horas": 0.1,
                    "max_horas": 168,  # 1 week
                    "p25_horas": 0.8,
                    "p75_horas": 6.2,
                },
                "distribucion": [
                    {"rango": "0-1 hora", "porcentaje": "45%"},
                    {"rango": "1-6 horas", "porcentaje": "32%"},
                    {"rango": "6-24 horas", "porcentaje": "16%"},
                    {"rango": "24+ horas", "porcentaje": "7%"},
                ],
                "interpretacion": "Muy rápido - cluster altamente engagado",
            }

            self.logger.info(f"Duration: {results['duracion_promedio_horas']}h avg")
            return results

        except Exception as e:
            self.logger.error(f"Error in bono_duracion_media: {str(e)}")
            return {"error": str(e)}
