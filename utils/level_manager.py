import yaml
import os

class LevelManager:
    def __init__(self, save_dir="saves", default_file="quicksave.yaml"):
        self.save_dir = save_dir
        self.default_save_path = os.path.join(self.save_dir, default_file)
        # Ensure the saves directory exists
        os.makedirs(self.save_dir, exist_ok=True)

    def save_level(self, entities, flow_name=None, metadata=None, filepath=None):
        """
        Saves the flow into a project directory structure or a custom filepath.
        Default: saves/[Flow_Name]/[Flow_Name].yaml
        """
        if metadata is None:
            metadata = {}
            
        if filepath:
            path = filepath
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            flow_name = flow_name or metadata.get("name", "Recorded_Test")
        else:
            if not flow_name:
                flow_name = metadata.get("flow_name", metadata.get("name", "Untitled_Flow"))
            
            # Normalize flow name for directory
            flow_dir_name = flow_name.replace(" ", "_")
            project_dir = os.path.join(self.save_dir, flow_dir_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Ensure subdirectories for assets
            for sub in ["icons", "sprites", "images"]:
                os.makedirs(os.path.join(project_dir, sub), exist_ok=True)
                
            path = os.path.join(project_dir, f"{flow_dir_name}.yaml")

        level_data = []
        for entity in entities:
            # Skip entities without a body or variant_key (diagnostic/non-persistent objects)
            if not getattr(entity, "body", None) or not hasattr(entity, "variant_key"):
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
            
        connections = []
        for entity in entities:
            if hasattr(entity, 'connected_uuids') and entity.connected_uuids:
                for target_uuid in entity.connected_uuids:
                    connections.append({"sender": entity.uuid, "receiver": target_uuid})
            
        # Include metadata at the root as requested
        full_data = {
            "name": flow_name,
            "description": metadata.get("description", metadata.get("flow_description", "")),
            "gravity": metadata.get("gravity", [0, 900]),
            "damping": metadata.get("damping", 0.99),
            "wind": metadata.get("wind", [0, 0]),
            "entities": level_data, 
            "connections": connections
        }
        
        # Add any other metadata keys if present
        for k, v in metadata.items():
            if k not in full_data and k not in ["flow_name", "flow_description"]:
                full_data[k] = v

        try:
            with open(path, "w") as f:
                yaml.dump(full_data, f, sort_keys=False)
            print(f"LevelManager: Successfully saved project '{flow_name}' to {path}")
        except Exception as e:
            print(f"LevelManager: Failed to save to {path}: {e}")

    def load_level(self, filepath=None):
        """
        Reads a YAML file and returns a tuple (entity_data, constraints_data, connections_data, metadata).
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
                
                # Metadata might be at root or in "metadata" key
                if "metadata" in data:
                    metadata = data.pop("metadata")
                else:
                    metadata = {
                        "name": data.get("name", data.get("flow_name", "Untitled")),
                        "description": data.get("description", data.get("flow_description", "")),
                        "gravity": data.get("gravity", [0, 900]),
                        "damping": data.get("damping", 0.99),
                        "wind": data.get("wind", [0, 0])
                    }
                    # Include other root keys in metadata except reserved ones
                    for k, v in data.items():
                        if k not in ["entities", "connections", "constraints", "name", "description", "flow_name", "flow_description", "gravity", "damping", "wind"]:
                            metadata[k] = v

                entities_data = data.get("entities", [])
                constraints_data = data.get("constraints", [])
                connections_data = data.get("connections", [])
                
                print(f"LevelManager: Successfully loaded {len(entities_data)} entities and metadata from {path}")
                return entities_data, constraints_data, connections_data, metadata
        except Exception as e:
            print(f"LevelManager: Failed to load from {path}: {e}")
            return [], [], [], {}
