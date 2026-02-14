from langgraph.graph import StateGraph, END
from agents.langgraph.state import AgentState

from agents.langgraph.nodes.thinking_node import thinking_node
from agents.langgraph.nodes.decision_router import decision_router
from agents.langgraph.nodes.llm_node import llm_node
from agents.langgraph.nodes.tool_executor import tool_executor
from agents.langgraph.nodes.tool_feedback import tool_feedback
from agents.langgraph.nodes.memory_loader import memory_loader
from agents.langgraph.nodes.memory_classifier import memory_classifier
from agents.langgraph.nodes.memory_summarizer import memory_summarizer
from agents.langgraph.nodes.memory_writer import memory_writer

graph = StateGraph(AgentState)

# nodes
graph.add_node("thinking", thinking_node)
graph.add_node("decision", decision_router)
graph.add_node("memory_loader", memory_loader)
graph.add_node("llm", llm_node)
graph.add_node("tool_executor", tool_executor)
graph.add_node("tool_feedback", tool_feedback)
graph.add_node("memory_classifier", memory_classifier)
graph.add_node("memory_summarizer", memory_summarizer)
graph.add_node("memory_writer", memory_writer)

# entry
graph.set_entry_point("thinking")

# flow
graph.add_edge("thinking", "decision")
graph.add_edge("decision", "memory_loader")
graph.add_edge("memory_loader", "llm")

graph.add_conditional_edges(
    "llm",
    lambda s: "tool_executor" if s.get("tool_call") else "memory_classifier"
)

graph.add_edge("tool_executor", "tool_feedback")
graph.add_edge("tool_feedback", "memory_classifier")

# conditional memory path
graph.add_conditional_edges(
    "memory_classifier",
    lambda s: "memory_summarizer" if s.get("should_store_memory") else END
)

graph.add_edge("memory_summarizer", "memory_writer")
graph.add_edge("memory_writer", END)

agent_app = graph.compile()
