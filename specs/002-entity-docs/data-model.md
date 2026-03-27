# Documentation Schema: Entity Component

For every entity listed in `config/entities.yaml`, the documentation file `docs/entity/[variant_key].md` must adhere precisely to the following template:

## Template Schema

```markdown
# [Entity Label]
**Category**: [Category]  
**Key Bind**: [Key Bind if defined, else N/A]

[Brief synthesized description of what the entity does in the physics/logic simulation].

## Required Properties
- `template`: [Which underlying Pymunk/Pygame primitive this uses]
- `width`/`height` or `radius`: [Dimensions based on template]
- `is_static`: [Boolean defining if Pymunk controls its kinematics]
- *(Other mandatory fields specifically required by this variant's logic)*

## Optional Properties & Defaults
- `color`: `[default from entities.yaml if any]`
- `mass`: `1.0` (for dynamic objects)
- `friction`: `0.5`
- `elasticity`: `0.5`
- *(Other optional logical fields available per entities.yaml)*
```
