import yaml
import os

class LevelManager:
    def __init__(self, save_dir="saves", default_file="quicksave.yaml"):
        self.save_dir = save_dir
        self.default_save_path = os.path.join(self.save_dir, default_file)
        # Ensure the saves directory exists
        os.makedirs(self.save_dir, exist_ok=True)

    def save_level(self, entities, constraints=None, filepath=None, metadata=None):
        """
        Extracts entity data from active entities and writes to a JSON file.
        """
        path = filepath if filepath else self.default_save_path
        level_data = []
        
        for entity in entities:
            if not getattr(entity, "body", None):
                continue
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
            
        # Phase 4: M17 Logic Connections
        connections = []
        for entity in entities:
            if hasattr(entity, 'connected_uuids') and entity.connected_uuids:
                for target_uuid in entity.connected_uuids:
                    connections.append({"sender": entity.uuid, "receiver": target_uuid})
            
        full_data = {
            "metadata": metadata if metadata else {},
            "entities": level_data, 
            "constraints": constraint_data, 
            "connections": connections
        }

        try:
            with open(path, "w") as f:
                yaml.dump(full_data, f, sort_keys=False)
            print(f"LevelManager: Successfully saved {len(entities)} entities to {path}")
        except Exception as e:
            print(f"LevelManager: Failed to save to {path}: {e}")

    def load_level(self, filepath=None):
        """
        Reads a JSON file and returns a tuple (entity_data, constraints_data, connections_data, metadata).
        Returns empty lists if the file doesn't exist.
        """
        path = filepath if filepath else self.default_save_path
        
        if not os.path.exists(path):
            print(f"LevelManager: Save file not found at {path}")
            return [], [], [], {}
            
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if not data:
                    return [], [], [], {}
                
                metadata = data.get("metadata", {})
                entities_data = data.get("entities", [])
                constraints_data = data.get("constraints", [])
                connections_data = data.get("connections", [])
                
                print(f"LevelManager: Successfully loaded {len(entities_data)} entities and metadata from {path}")
                return entities_data, constraints_data, connections_data, metadata
        except Exception as e:
            print(f"LevelManager: Failed to load from {path}: {e}")
            return [], [], [], {}
