Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into an implementation plan.

Context:
We have an approved specification for Milestone 13: Object Relationships & Constraints (docs/SPECIFICATION_M13_Relationships.md). This milestone introduces a Relational Architecture (UUIDs, two-pass spawning, cascading deletion) to support Pymunk joints like pulleys and ropes.

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M13_Relationships.md.

Requirements for the Implementation Plan:

Lightweight & High-Level: Provide a high-level sequence of phases.

Suggested Phases:

Phase 1: UUID System & State Tracking (Assigning IDs to instantiated entities).

Phase 2: Relational YAML Parsing (Updating the config reader to parse constraint data).

Phase 3: Two-Pass Spawning System (Refactoring level loading and tool spawning to instantiate bodies first, then apply constraints).

Phase 4: Cascading Deletion (Updating the M11 deletion logic to safely destroy attached Pymunk constraints before removing bodies).

Autonomy for the Coder: Leave the exact Python logic (like the specific pymunk constraint parameters and dictionary mapping implementation) up to the Implementation Agent.

Actionable Goals: Each phase should describe the goal, the files likely involved (e.g., main.py, entities/base.py, utils/level_manager.py), and a brief acceptance check.

Output Format:

Produce a lightweight Markdown document outlining the phased task list.

CRITICAL CONSTRAINT: Do NOT generate any Python code.