from app.core.memory.mem0_memory import Mem0Memory

memory = Mem0Memory()

memory.memory.add(
    "Ajay prefers PostgreSQL for LangGraph checkpoints.",
    user_id="ajay",
)

result = memory.memory.search(
    "What database does Ajay prefer for LangGraph checkpoints?",
    filters={"user_id": "ajay"}
)

print(result)