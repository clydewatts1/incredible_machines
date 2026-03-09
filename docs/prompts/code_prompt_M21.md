Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

docs/SPECIFICATION_M21_CanvasProperties.md

docs/IMPLEMENTATION_PLAN_M21_CanvasProperties.md

Task: Implement Milestone 21: Canvas Properties & Environments. Execute the phased steps outlined in the implementation plan.

Critical Instructions:

Allow autonomy in execution: Rely on your own expertise to integrate the UI text boxes (from M14) to edit the global dictionary of canvas settings.

Robust Parsing: When reading gravity/damping from the UI text inputs or the YAML file, ensure robust type casting (convert to floats) to prevent Pymunk crashes.

Rendering Order: The custom background image/color MUST be drawn inside the playable_rect before the grid lines (if any) and before the entities, but after the global window background.

Fallback Defaults: If an older level save file is loaded that does not contain a canvas_settings block, your load function must cleanly apply default values (e.g., gravity (0, 900), damping 0.99) instead of throwing a KeyError.