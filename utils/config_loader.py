import yaml
import os
import sys

def load_entity_config(property_key):
    """
    Loads entity properties from config/entities.yaml using deep merge inheritance.
    Fails loudly if the file, template, or key are missing.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'entities.yaml')
    
    if not os.path.exists(config_path):
        print(f"FAIL LOUDLY: Missing config file at {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
        
    templates = data.get("templates", {})
    variants = data.get("variants", {})
        
    if property_key not in variants:
        print(f"FAIL LOUDLY: YAML missing requested variant key: '{property_key}'.")
        sys.exit(1)
        
    variant_data = variants[property_key]
    template_key = variant_data.get("template")
    
    if not template_key or template_key not in templates:
        print(f"FAIL LOUDLY: Variant '{property_key}' is missing a valid template '{template_key}'.")
        sys.exit(1)
        
    # Start with template defaults, overwrite with specifics (Deep Merge)
    properties = templates[template_key].copy()
    properties.update(variant_data)
    
    return properties

def load_all_variants():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'entities.yaml')
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get("variants", {})
