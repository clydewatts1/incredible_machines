Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into an implementation plan.

Context:
We have an approved specification for Milestone 12: Active Entities (Cannon & Basket) (docs/SPECIFICATION_M12_ActiveEntities.md).

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M12_ActiveEntities.md.

Requirements for the Implementation Plan:

Lightweight & High-Level: Provide a high-level sequence of phases.

Suggested Phases: * Phase 1: YAML Configuration (adding the Cannon and Basket data).

Phase 2: Composite Geometry parsing (updating entity creation to support U-shapes/multiple shapes per body).

Phase 3: Cannon Spawning Logic (timers and PLAY state checks).

Phase 4: Basket Ingestion Logic (Pymunk sensors and collision handlers).

Autonomy for the Coder: Leave the exact math for the composite shapes and collision callback structuring up to the Implementation Agent.

Actionable Goals: Each phase should describe the goal, the files likely involved (config/entities.yaml, entities/base.py, main.py), and a brief acceptance check.

Output Format:

Produce a lightweight Markdown document outlining the phased task list.

CRITICAL CONSTRAINT: Do NOT generate any Python code.