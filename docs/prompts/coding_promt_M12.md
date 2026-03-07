Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md (Specifically sections regarding Data-Driven Design, State Machine, and Pymunk Authority)

docs/SPECIFICATION_M12_ActiveEntities.md

docs/IMPLEMENTATION_PLAN_M12_ActiveEntities.md

Task: Implement Milestone 12: Active Entities (Cannon & Basket). Execute the phased steps outlined in the implementation plan.

Critical Instructions:

Allow autonomy in execution: Rely on your own expertise to build the composite U-shapes (3 segments per body) and set up the Pymunk collision handlers.

Ensure the Cannon only fires when the game state is actively in PLAY mode.

Ensure the Basket's ingestion safely removes objects from both the Pymunk space and the Pygame render list without crashing the simulation step.