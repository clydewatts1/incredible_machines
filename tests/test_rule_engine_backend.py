import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.engines import create_engine

def test_rule_engine_basic():
    print("Running test_rule_engine_basic...")
    instructions = {
        "engine_type": "rule_engine",
        "default_state": 0,
        "rules": [
            {"condition": "score >= 50 and type == 'admin'", "state": 1},
            {"condition": "score < 50", "state": 2}
        ]
    }
    
    engine = create_engine("rule_engine", instructions)
    
    # Match rule 1
    payload1 = {"score": 75, "type": "admin"}
    res1 = engine.process(payload1, instructions)
    print(f"Payload1: {payload1} -> Result: {res1} (Expected: 1)")
    assert res1 == 1
    
    # Match rule 2
    payload2 = {"score": 25, "type": "user"}
    res2 = engine.process(payload2, instructions)
    print(f"Payload2: {payload2} -> Result: {res2} (Expected: 2)")
    assert res2 == 2
    
    # Default state (admin but low score)
    payload3 = {"score": 40, "type": "admin"}
    res3 = engine.process(payload3, instructions)
    print(f"Payload3: {payload3} -> Result: {res3} (Expected: 2)") # Matches score < 50
    assert res3 == 2

    # Default state (no match)
    instructions_no_fallback = {
        "engine_type": "rule_engine",
        "default_state": 99,
        "rules": [
            {"condition": "type == 'root'", "state": 1}
        ]
    }
    engine2 = create_engine("rule_engine", instructions_no_fallback)
    payload4 = {"type": "guest"}
    res4 = engine2.process(payload4, instructions_no_fallback)
    print(f"Payload4: {payload4} -> Result: {res4} (Expected: 99)")
    assert res4 == 99

def test_rule_engine_flattening():
    print("\nRunning test_rule_engine_flattening...")
    instructions = {
        "engine_type": "rule_engine",
        "default_state": 0,
        "rules": [
            {"condition": "amount > 1000", "state": 10}
        ]
    }
    engine = create_engine("rule_engine", instructions)
    
    # Data is inside a nested 'data' dict
    payload = {
        "uuid": "ball_01",
        "data": {"amount": 5000}
    }
    res = engine.process(payload, instructions)
    print(f"Nested Payload: {payload} -> Result: {res} (Expected: 10)")
    assert res == 10

def test_rule_engine_error():
    print("\nRunning test_rule_engine_error...")
    instructions = {
        "engine_type": "rule_engine",
        "rules": [
            {"condition": "!!! invalid syntax !!!", "state": 1}
        ]
    }
    engine = create_engine("rule_engine", instructions)
    res = engine.process({"val": 1}, instructions)
    print(f"Error Result: {res}")
    assert "fatal: rule_engine error" in str(res)

if __name__ == "__main__":
    try:
        test_rule_engine_basic()
        test_rule_engine_flattening()
        test_rule_engine_error()
        print("\n✅ All RuleEngine tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
