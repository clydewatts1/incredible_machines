import sys
import os
import json
import shutil
import pymunk

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.engines import create_engine
from entities.file_sink import FileSink

def test_faker_engine():
    print("Testing FakerEngine mutation...")
    instructions = {
        "engine_type": "faker",
        "schema": {
            "job": "job",
            "company": "company"
        },
        "state": 10
    }
    engine = create_engine("faker", instructions)
    
    payload = {"data": {"name": "Test User"}}
    res = engine.process(payload, instructions)
    
    print(f"Result State: {res}")
    print(f"Mutated Payload: {payload}")
    
    assert res == 10
    assert "job" in payload["data"]
    assert "company" in payload["data"]
    assert payload["data"]["name"] == "Test User"

def test_file_sink():
    print("\nTesting FileSink export...")
    test_dir = "exports/test_synthetic"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    space = pymunk.Space()
    sink = FileSink(space, 0, 0)
    sink.properties["output_directory"] = test_dir
    
    class MockPayload:
        def __init__(self):
            self.uuid = "test_uuid_123"
            self.payload = {"data": {"name": "Faker Test", "job": "Engineer"}}
            self.to_delete = False
            
    payload_entity = MockPayload()
    sink.ingest_payload(payload_entity)
    
    filepath = os.path.join(test_dir, f"record_{payload_entity.uuid}.json")
    print(f"Checking for file: {filepath}")
    assert os.path.exists(filepath)
    
    with open(filepath, "r") as f:
        data = json.load(f)
        print(f"File Content: {data}")
        assert data["name"] == "Faker Test"
        assert data["job"] == "Engineer"
    
    assert payload_entity.to_delete is True

if __name__ == "__main__":
    try:
        test_faker_engine()
        test_file_sink()
        print("\n✅ Faker Pipeline Backend tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
