import os
import yaml
import glob
import re

TESTS_DIR = "tests"
DOCS_DIR = "docs/entity"

def load_yaml(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def extract_existing_content(filepath):
    if not os.path.exists(filepath):
        return "An entity component.", "Summary goes here.", "Detail goes here."
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Heuristics to grab what we can from existing text
    description = ""
    # Try to grab text before any headers
    lines = content.split('\n')
    text_lines = []
    for line in lines:
        if line.strip().startswith('##'):
            break
        if not line.strip().startswith('#') and not line.strip().startswith('**'):
            if line.strip():
                text_lines.append(line.strip())
    
    description = " ".join(text_lines) if text_lines else "An entity component."
    return description, "Summary goes here.", "Detail goes here."

def determine_proper_name(entity_id):
    parts = entity_id.split('_')
    return " ".join([p.capitalize() for p in parts])

def get_key_bind(entity_id):
    # Quick static mapping based on common keybinds, mostly N/A for now.
    binds = {
        'bouncy_ball': 'B',
        'payload_ball': 'P',
        'box': 'Left Click',
        'conveyor_belt': 'C',
    }
    return binds.get(entity_id, "N/A")

def rewrite_doc(entity_id, data):
    doc_path = os.path.join(DOCS_DIR, f"{entity_id}.md")
    desc, summary, detail = extract_existing_content(doc_path)
    
    # Grab entity data
    ent_data = data.get('entities', [{}])[0]
    overrides = ent_data.get('overrides', {})
    
    proper_name = determine_proper_name(entity_id)
    category = overrides.get('category', 'unknown')
    key_bind = get_key_bind(entity_id)
    
    out = []
    out.append(f"# {proper_name}")
    out.append(f"**Category**: {category}  ")
    out.append(f"**Key Bind**: {key_bind}")
    out.append("")
    out.append("## Description")
    out.append(desc)
    out.append("")
    out.append("## Summary")
    out.append(summary)
    out.append("")
    out.append("## Detail")
    out.append(detail)
    out.append("")
    out.append("## Parameters and Functionality")
    out.append("")
    
    # Separate properties into functional groups if possible
    animations = overrides.pop('animations', None)
    instructions = overrides.pop('instructions', None)
    sounds = overrides.pop('sounds', None)
    export_cfg = overrides.pop('export', None)
    
    out.append("### Baseline Properties")
    out.append(f"- `template`: {overrides.get('template', 'Unknown')}")
    out.append(f"- `is_static`: {overrides.get('is_static', 'False')}")
    
    out.append("")
    out.append("### Additional Parameters")
    for k, v in sorted(overrides.items()):
        if k not in ['template', 'is_static', 'category', 'label', 'custom_name', 'custom_description', 'uuid']:
            out.append(f"- `{k}`: `{v}`")
            
    if instructions:
        out.append("")
        out.append("### Instructions Context")
        for k, v in instructions.items():
            out.append(f"- `{k}`: `{v}`")
            
    if animations:
        out.append("")
        out.append("### Animation States")
        for k, v in animations.items():
            out.append(f"- `{k}`: `{v}`")
            
    if export_cfg:
        out.append("")
        out.append("### Export Configuration")
        for k, v in export_cfg.items():
            out.append(f"- `{k}`: `{v}`")

    with open(doc_path, 'w') as f:
        f.write("\n".join(out))

def main():
    test_files = glob.glob(os.path.join(TESTS_DIR, "single_entity_*", "*.yaml"))
    
    for tf in test_files:
        try:
            data = load_yaml(tf)
            if not data or 'entities' not in data or not data['entities']:
                continue
            entity_id = data['entities'][0].get('entity_id')
            if entity_id:
                rewrite_doc(entity_id, data)
                print(f"Updated docs/entity/{entity_id}.md")
        except Exception as e:
            print(f"Failed processing {tf}: {e}")

if __name__ == "__main__":
    main()
