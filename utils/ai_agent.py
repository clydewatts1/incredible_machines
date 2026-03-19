"""
Local AI Agent Engine
---------------------
Stack: 
- Inference: Ollama (running locally at localhost:11434)
- Framework: Pure Python
- Vector DB: ChromaDB (in-memory/local SQLite)
- Structured Output: Pydantic

Prerequisites:
    pip install openai pydantic chromadb
    Ensure Ollama is installed and run: `ollama run llama3.1`
"""

import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from openai import OpenAI
import chromadb

# ==========================================
# 1. Pydantic Schema (Guided Decoding)
# ==========================================
# This forces the local LLM to output perfect JSON that matches this exact structure.
# It will never hallucinate random text or missing brackets.
class AgentAction(BaseModel):
    thought: str = Field(description="The agent's internal reasoning for the chosen action.")
    tool_name: str = Field(description="The exact name of the tool to execute.")
    tool_args: Dict[str, Any] = Field(description="The JSON arguments to pass to the tool.")

# ==========================================
# 2. Tool Registry (The "Hands")
# ==========================================
# These are standard Python functions that interact with your game or system.
def spawn_game_entity(variant_key: str, x: int, y: int) -> dict:
    print(f"🔧 [Game Engine] Spawning {variant_key} at ({x}, {y})...")
    # In reality, this would call your main.py create_part() function
    return {"status": "success", "uuid": "new_entity_123"}

def fix_conveyor_belt(belt_id: str) -> dict:
    print(f"🔧 [Game Engine] Applying fix to conveyor belt: {belt_id}...")
    return {"status": "success", "cleared_jam": True}

# Map string names to actual Python functions
TOOL_REGISTRY = {
    "spawn_game_entity": spawn_game_entity,
    "fix_conveyor_belt": fix_conveyor_belt,
    "none": lambda: {"status": "idle", "message": "No action required."}
}

# ==========================================
# 3. The Core Agent Engine
# ==========================================
class LocalAgentEngine:
    def __init__(self, model_name: str = "llama3.1"):
        # We use the standard OpenAI client but point it to the local Ollama API!
        self.client = OpenAI(
            base_url="http://localhost:11434/v1", 
            api_key="ollama" # required but ignored by Ollama
        )
        self.model = model_name

        # Initialize local ChromaDB for memory retrieval
        self.chroma_client = chromadb.Client()
        self.memory = self.chroma_client.get_or_create_collection(name="agent_long_term_memory")
        print(f"🤖 Agent Engine Initialized (Model: {self.model})")

    def teach_concept(self, memory_id: str, concept_text: str):
        """Injects documentation or past experiences into the Vector DB."""
        self.memory.add(documents=[concept_text], ids=[memory_id])
        print(f"🧠 Learned new concept: {memory_id}")

    def _retrieve_context(self, query: str, n_results: int = 1) -> str:
        """Searches ChromaDB for relevant memories based on the current observation."""
        if self.memory.count() == 0:
            return "No relevant memories found."
        
        results = self.memory.query(query_texts=[query], n_results=n_results)
        documents = results.get("documents", [[]])[0]
        return "\n".join(documents)

    def run_cycle(self, observation: str):
        """The core ReAct loop: Observe -> Retrieve Context -> Think -> Act"""
        print("\n" + "="*50)
        print(f"👀 OBSERVATION: {observation}")
        print("="*50)

        # 1. Retrieve Context
        context = self._retrieve_context(observation)
        print(f"📚 RECALLED CONTEXT:\n{context}\n")

        # 2. Build the Prompt
        system_prompt = f"""
        You are an autonomous AI managing a physics puzzle game.
        Your goal is to analyze the observation, reason about it, and select the appropriate tool.
        
        Available Tools:
        - spawn_game_entity(variant_key, x, y): Spawns an item.
        - fix_conveyor_belt(belt_id): Fixes a jammed belt.
        - none(): Do nothing.
        
        Relevant Game Manual/Memory:
        {context}
        """

        # 3. Inference (Call Ollama with Guided Decoding)
        print("🤔 Thinking... (Waiting for local inference)")
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Observation: {observation}"}
                ],
                response_format=AgentAction, # <--- THIS ENFORCES THE PYDANTIC SCHEMA!
            )
            
            # Extract the perfectly formatted Pydantic object
            action: AgentAction = response.choices[0].message.parsed
            
            print(f"💡 THOUGHT: {action.thought}")
            print(f"🎯 INTENT: Call '{action.tool_name}' with args: {action.tool_args}\n")

            # 4. Action Execution
            tool_func = TOOL_REGISTRY.get(action.tool_name)
            if tool_func:
                result = tool_func(**action.tool_args)
                print(f"✅ ACTION RESULT: {result}")
            else:
                print(f"❌ ERROR: Hallucinated or invalid tool name '{action.tool_name}'")

        except Exception as e:
            print(f"⚠️ Inference Error: {e}")

# ==========================================
# 4. Test the Engine
# ==========================================
if __name__ == "__main__":
    # Initialize the engine
    engine = LocalAgentEngine(model_name="llama3.1") # or "qwen2.5-coder" if you pulled it

    # Give the agent some long-term memory about how the game works
    engine.teach_concept(
        "factory_rules", 
        "If a machine needs a logic component to process payloads, spawn a 'logic_factory' entity."
    )
    engine.teach_concept(
        "jam_protocol", 
        "If a conveyor belt is jammed, you must use the fix_conveyor_belt tool."
    )

    # Simulate an event triggering the agent (e.g., from your Pygame DataSink)
    print("\n--- Simulating Game Event 1 ---")
    engine.run_cycle("Alert! The conveyor belt 'belt_404' has stopped moving and objects are piling up.")

    print("\n--- Simulating Game Event 2 ---")
    engine.run_cycle("The user clicked a button requesting a new payload processor at coordinates x=500, y=300.")