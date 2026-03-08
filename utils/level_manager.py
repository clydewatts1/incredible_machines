import yaml
import os

class LevelManager:
    def __init__(self, save_dir="saves", default_file="quicksave.yaml"):
        self.save_dir = save_dir
        self.default_save_path = os.path.join(self.save_dir, default_file)
        # Ensure the saves directory exists
        os.makedirs(self.save_dir, exist_ok=True)

    def save_level(self, entities, constraints=None, filepath=None):
        """
        Extracts entity data from active entities and writes to a JSON file.
        """
        path = filepath if filepath else self.default_save_path
        level_data = []
        
        for entity in entities:
            data = {
                "uuid": entity.uuid,
                "entity_id": entity.variant_key,
                "position": {
                    "x": entity.body.position.x,
                    "y": entity.body.position.y
                },
                "rotation": entity.body.angle,
                "overrides": entity.overrides
            }
            level_data.append(data)
            
        if constraints is None:
            constraints = []
        constraint_data = []
        for c in constraints:
            # We will populate constraint data serialization in Phase 3/4
            pass
            
        try:
            with open(path, "w") as f:
                yaml.dump({"entities": level_data, "constraints": constraint_data}, f, sort_keys=False)
            print(f"LevelManager: Successfully saved {len(entities)} entities to {path}")
        except Exception as e:
            print(f"LevelManager: Failed to save to {path}: {e}")

    def load_level(self, filepath=None):
        """
        Reads a JSON file and returns a tuple (entity_data, constraints_data).
        Returns empty lists if the file doesn't exist.
        """
        path = filepath if filepath else self.default_save_path
        
        if not os.path.exists(path):
            print(f"LevelManager: Save file not found at {path}")
            return [], []
            
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                entities_data = data.get("entities", []) if data else []
                constraints_data = data.get("constraints", []) if data else []
                print(f"LevelManager: Successfully loaded {len(entities_data)} entities and {len(constraints_data)} constraints from {path}")
                return entities_data, constraints_data
        except Exception as e:
            print(f"LevelManager: Failed to load from {path}: {e}")
            return [], []
