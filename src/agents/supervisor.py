"""
Supervisor Agent - Main Orchestrator for RFM-LDE Multiagent

LangGraph-based supervisor that:
1. Receives user message + conversation history
2. Analyzes which specialists are needed
3. Routes to appropriate specialists
4. Aggregates results
5. Generates response

This is the core orchestrator that coordinates all specialist agents.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class DecisionSupervisor(BaseModel):
    """
    LLM output for supervisor decision routing.

    Tells the graph which specialists to call and what parameters to use.
    """
    cluster: Optional[int] = Field(None, ge=0, le=3, description="Target cluster 0-3")
    quintil: Optional[int] = Field(None, ge=1, le=5, description="Target quintile 1-5")
    run_date: str = Field(default="latest", description="YYYY-MM-DD or 'latest'")
    period: Dict[str, str] = Field(default_factory=lambda: {"type": "relative", "value": "last_week"})
    specialists_needed: List[str] = Field(
        default_factory=list,
        description="List of specialists: aadd, bonos, depositos_retiros, ventas_ggw, exportar, grafico, metodologia"
    )
    needs_clarification: bool = Field(False, description="True if cluster/quintile ambiguous")
    clarification_question: Optional[str] = None


class Supervisor:
    """
    Supervisor agent orchestrating all specialists via LangGraph.

    Responsibilities:
    - Parse user queries
    - Route to appropriate specialists
    - Coordinate multi-specialist queries
    - Manage conversation state
    - Format final response
    """

    def __init__(self, llm_client=None, specialists: Dict[str, Any] = None):
        """
        Initialize supervisor with LLM and specialists.

        Args:
            llm_client: Anthropic client for Claude calls
            specialists: Dict of specialist instances {name: specialist_obj}
        """
        self.llm_client = llm_client
        self.specialists = specialists or {}
        self.logger = logger
        self.graph = self._build_langgraph()

    def _build_langgraph(self):
        """
        Build LangGraph workflow for multi-agent coordination.

        Graph flow:
        START → INIT_TURN → SUPERVISOR_DECISION → ROUTE_SPECIALISTS
               → EXECUTE_SPECIALISTS → AGGREGATE_RESULTS → RESPONDER → END

        Returns:
            Compiled LangGraph
        """
        workflow = StateGraph(dict)

        # Node 1: Initialize turn (clear results, increment step counter)
        def init_turn(state):
            """Reset results and initialize turn state"""
            state["resultados"] = {}
            state["pasos"] = state.get("pasos", 0) + 1
            state["paso_actual"] = "init_turn"
            self.logger.info(f"Turn {state['pasos']}: Initialized")
            return state

        # Node 2: Supervisor decision (LLM routing)
        async def supervisor_decision(state):
            """
            Use LLM to decide which specialists to call.

            Calls Claude to analyze the user query and decide routing.
            """
            user_message = state["historial"][-1]["content"]

            # Build prompt for supervisor decision
            decision_prompt = f"""
            You are the supervisor routing agent for a player clustering system.

            Current cluster/quintile group: {state.get('grupo', 'Not specified')}
            User message: {user_message}
            Conversation history length: {len(state.get('historial', []))} messages

            Decide which specialists to call (choose from: aadd, bonos, depositos_retiros, ventas_ggw, exportar, grafico, metodologia)
            Also specify: cluster (0-3 or None), quintil (1-5 or None)

            Return JSON with decision.
            """

            # In production, call Claude API via llm_client
            # decision = await self.llm_client.messages.create(...)

            # Mock decision for demonstration
            decision = {
                "cluster": state.get("grupo", {}).get("cluster"),
                "quintil": state.get("grupo", {}).get("quintil"),
                "specialists_needed": ["aadd", "grafico"] if "aadd" in user_message.lower() else ["metodologia"],
                "needs_clarification": False,
            }

            state["decision"] = decision
            state["paso_actual"] = "supervisor_decision"
            self.logger.info(f"Decision: call {len(decision['specialists_needed'])} specialists")
            return state

        # Node 3: Execute specialists
        async def execute_specialists(state):
            """
            Call each required specialist agent.

            Runs specialists in parallel (could use asyncio.gather in production)
            """
            results = {}
            decision = state.get("decision", {})
            specialists_needed = decision.get("specialists_needed", [])

            for spec_name in specialists_needed:
                if spec_name not in self.specialists:
                    self.logger.warning(f"Specialist {spec_name} not found")
                    continue

                specialist = self.specialists[spec_name]

                try:
                    # Call specialist method
                    if spec_name == "aadd":
                        result = await specialist.consultar_apuestas_aadd(
                            cluster=state.get("grupo", {}).get("cluster", 0),
                            quintil=state.get("grupo", {}).get("quintil", 3),
                            periodo=state.get("periodo", {})
                        )
                    elif spec_name == "bonos":
                        result = await specialist.consultar_bonos(
                            cluster=state.get("grupo", {}).get("cluster", 0),
                            quintil=state.get("grupo", {}).get("quintil", 3),
                            periodo=state.get("periodo", {})
                        )
                    elif spec_name == "grafico":
                        result = await specialist.perfil_clusters(
                            cluster=state.get("grupo", {}).get("cluster", 0)
                        )
                    else:
                        result = {"status": "ok", "specialist": spec_name}

                    results[spec_name] = result
                    self.logger.info(f"✓ {spec_name} completed")

                except Exception as e:
                    self.logger.error(f"Error in {spec_name}: {str(e)}")
                    results[spec_name] = {"error": str(e)}

            state["resultados"] = results
            state["paso_actual"] = "execute_specialists"
            return state

        # Node 4: Generate response
        def responder(state):
            """
            Format final response with all specialist results.

            Creates natural language response in Spanish.
            """
            results = state.get("resultados", {})
            user_message = state["historial"][-1]["content"]

            # Build response from results
            response_parts = []

            if "aadd" in results:
                aadd_data = results["aadd"]
                if "error" not in aadd_data:
                    response_parts.append(
                        f"En AADD: {aadd_data.get('total_apuestas', 0)} apuestas, "
                        f"S/ {aadd_data.get('volumen_total', 0):.2f} volumen"
                    )

            if "bonos" in results:
                bonos_data = results["bonos"]
                if "error" not in bonos_data:
                    response_parts.append(
                        f"Bonos: {bonos_data.get('total_bonos_activos', 0)} activos"
                    )

            if not response_parts:
                response = "No hay datos disponibles para esa consulta."
            else:
                response = " | ".join(response_parts)

            state["respuesta"] = response
            state["paso_actual"] = "responder"
            self.logger.info(f"Response: {response[:100]}...")
            return state

        # Add nodes to graph
        workflow.add_node("init_turn", init_turn)
        workflow.add_node("supervisor_decision", supervisor_decision)
        workflow.add_node("execute_specialists", execute_specialists)
        workflow.add_node("responder", responder)

        # Add edges
        workflow.set_entry_point("init_turn")
        workflow.add_edge("init_turn", "supervisor_decision")
        workflow.add_edge("supervisor_decision", "execute_specialists")
        workflow.add_edge("execute_specialists", "responder")
        workflow.add_edge("responder", END)

        # Compile graph
        return workflow.compile()

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the entire workflow.

        Args:
            state: Conversation state with historial, grupo, periodo

        Returns:
            Updated state with respuesta, resultados, pasos
        """
        self.logger.info(f"Starting turn with {len(state.get('historial', []))} messages")

        # Run the graph
        output = await self.graph.ainvoke(state)

        return output
