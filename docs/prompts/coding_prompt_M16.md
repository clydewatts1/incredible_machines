Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md

docs/SPECIFICATION_M16_AssetPipeline.md

docs/IMPLEMENTATION_PLAN_M16_AssetPipeline.md

Task: Implement Milestone 16: Asset Pipeline & Sprite Management. Execute the phased steps outlined in the implementation plan.

Critical Instructions:

Allow autonomy in execution: Rely on your own expertise to build a robust AssetManager class that handles caching to prevent memory leaks or frame drops.

File System Safety: Use os.makedirs(..., exist_ok=True) to ensure the assets/sprites/ and assets/icons/ directories exist before trying to load or save images to them.

Auto-Generation: The generated placeholder image must be visually distinct (e.g., a grey square with a large red X, or the entity name written on it) and it MUST be saved to the disk using pygame.image.save() so the user has a physical file they can edit and overwrite later.

Sprite Rotation: When blitting the sprite over the physics body, remember to calculate the bounding box offset correctly after using pygame.transform.rotate(), as Pygame rotates surfaces around their center and expands the bounding box, which can cause jitter if not centered to the Pymunk body's coordinates.