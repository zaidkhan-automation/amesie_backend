from langgraph.graph import StateGraph, END
from agents.langgraph.state import AgentState
from agents.langgraph.nodes.llm_node import llm_node
from agents.langgraph.nodes.tool_executor import tool_executor
from agents.langgraph.nodes.tool_feedback import tool_feedback

graph = StateGraph(AgentState)

graph.add_node("llm", llm_node)
graph.add_node("tool_executor", tool_executor)
graph.add_node("tool_feedback", tool_feedback)

graph.set_entry_point("llm")

graph.add_conditional_edges(
    "llm",
    lambda s: "tool_executor" if s.get("tool_call") else END
)

graph.add_edge("tool_executor", "tool_feedback")
graph.add_edge("tool_feedback", END)
agent_app = graph.compile()
