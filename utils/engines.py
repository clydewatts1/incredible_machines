import copy
import random
import re
try:
    import rule_engine
except ImportError:
    rule_engine = None

try:
    from faker import Faker
except ImportError:
    Faker = None
from typing import Any, Dict, List, Optional, Type


class BaseEngine:
    """Common contract for all factory engines."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config_dict = config_dict or {}

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
        # Milestone 35 Refinement: Global Mock Toggle for Testing
        import os
        if os.environ.get("TEST_MOCK_MODE") == "1":
            print(f"🤖 [MockEngine] Simulating processing for {instructions.get('engine_type', 'unknown')}...")
            return instructions.get("default_state", 0)
        raise NotImplementedError("Engines must implement process().")

    def validate_config(self, instructions: Optional[Dict[str, Any]] = None) -> bool:
        return True


class NullEngine(BaseEngine):
    """Graceful fallback engine when registry lookup fails."""

    def process(self, payload: Any, instructions: Dict[str, Any]) -> int:
        return int(instructions.get("default_state", 0))


class RegexEngine(BaseEngine):
    def validate_config(self, instructions: Optional[Dict[str, Any]] = None) -> bool:
        cfg = instructions or {}
        if not isinstance(cfg.get("rules", []), list):
            return False
        return True

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
        print(f"🎯 [RegexEngine] Processing payload '{payload}' with instructions {instructions}")
        rules = instructions.get("rules", [])
        default_state = int(instructions.get("default_state", 0))

        if not isinstance(rules, list):
            return "fatal: regex instructions.rules must be a list"

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            pattern = str(rule.get("pattern", ""))
            state = int(rule.get("state", default_state))
            print(f"🎯 [RegexEngine] Evaluating rule: pattern='{pattern}', state={state}")

            if isinstance(payload, dict):
                target_field = rule.get("target_field")
                print(f"🎯 [RegexEngine] Extracting target field '{target_field}' from payload")
                if not target_field:
                    return "fatal: missing target_field for dictionary payload"
                candidate_value = payload.get(str(target_field), "")
                if candidate_value == "":
                    # get the data field in payload - check if it is a dict and has the target_field as key
                    data_field = payload.get("data", {})
                    if isinstance(data_field, dict):
                        candidate_value = data_field.get(str(target_field), "")
                        
            print(f"🎯 [RegexEngine] Candidate value for regex matching: '{candidate_value}'")
            candidate_text = "" if candidate_value is None else str(candidate_value)

            try:
                if re.search(pattern, candidate_text):
                    print(f"🎯 [RegexEngine] Pattern matched! Returning state {state}")
                    return state
            except re.error as exc:
                return f"fatal: regex syntax error: {exc}"

        return default_state


class RandomEngine(BaseEngine):
    def validate_config(self, instructions: Optional[Dict[str, Any]] = None) -> bool:
        cfg = instructions or {}
        if cfg.get("distribution") not in {"uniform", "normal"}:
            return False
        return isinstance(cfg.get("rules", []), list)

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
        distribution = str(instructions.get("distribution", "uniform")).lower()
        params = instructions.get("params", {})
        rules = instructions.get("rules", [])
        default_state = int(instructions.get("default_state", 0))

        if not isinstance(params, dict):
            return "fatal: random params must be an object"
        if not isinstance(rules, list):
            return "fatal: random rules must be a list"

        try:
            if distribution == "normal":
                mu = float(params.get("mu", 50.0))
                sigma = float(params.get("sigma", 15.0))
                x = random.gauss(mu, sigma)
            elif distribution == "uniform":
                min_value = float(params.get("min", 0.0))
                max_value = float(params.get("max", 100.0))
                x = random.uniform(min_value, max_value)
            else:
                return f"fatal: unsupported distribution '{distribution}'"
        except (TypeError, ValueError) as exc:
            return f"fatal: random parameter error: {exc}"

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            try:
                threshold = float(rule.get("random"))
            except (TypeError, ValueError):
                continue
            if x < threshold:
                try:
                    return int(rule.get("state", default_state))
                except (TypeError, ValueError):
                    return default_state

        return default_state


class RuleEngine(BaseEngine):
    def validate_config(self, instructions: Optional[Dict[str, Any]] = None) -> bool:
        cfg = instructions or {}
        if rule_engine is None:
            return False
        if not isinstance(cfg.get("rules", []), list):
            return False
        return True

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
        if rule_engine is None:
            return "fatal: rule-engine library is not installed (run 'pip install rule-engine')"
        
        rules = instructions.get("rules", [])
        default_state = int(instructions.get("default_state", 0))
        
        if not isinstance(rules, list):
            return "fatal: rule_engine rules must be a list"

        for rule_def in rules:
            if not isinstance(rule_def, dict):
                continue
            
            condition = str(rule_def.get("condition", "false"))
            state = rule_def.get("state")
            
            try:
                # Rule-engine evaluates against a dictionary
                context = payload if isinstance(payload, dict) else {"payload": payload}
                
                # If it's a dict, also check for a 'data' field which is common in our payloads
                if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
                    # Flatten for easier querying
                    context = copy.deepcopy(payload)
                    for k, v in payload["data"].items():
                        context[k] = v
                
                rule = rule_engine.Rule(condition)
                if rule.evaluate(context):
                    return int(state) if state is not None else default_state
            except Exception as e:
                return f"fatal: rule_engine error: {e}"
        
        return default_state


class FakerEngine(BaseEngine):
    """
    Milestone 40: Synthetic Data Transformation Engine.
    Uses the Faker library to mutate or enrich payload content.
    """
    def validate_config(self, instructions: Optional[Dict[str, Any]] = None) -> bool:
        cfg = instructions or {}
        if Faker is None:
            return False
        return isinstance(cfg.get("schema", {}), dict)

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
        if Faker is None:
            return "fatal: faker library is not installed (run 'pip install faker')"
        
        schema = instructions.get("schema", {})
        state = int(instructions.get("state", 10))
        
        # Initialize Faker instance
        fake = Faker()
        seed = instructions.get("random_seed")
        if seed is not None:
            fake.seed_instance(int(seed))

        # Ensure we are working with a dict
        if not isinstance(payload, dict):
             return "fatal: faker engine requires a dictionary payload"
        
        # Use nested 'data' field if present (standard pattern in original code)
        target = payload
        if "data" in payload and isinstance(payload["data"], dict):
            target = payload["data"]

        for key, provider in schema.items():
            try:
                method = getattr(fake, str(provider))
                target[key] = method()
            except Exception as e:
                return f"fatal: faker error for {key}/{provider}: {e}"
        
        return state


ENGINE_REGISTRY: Dict[str, Type[BaseEngine]] = {
    "regex": RegexEngine,
    "random": RandomEngine,
    "rule_engine": RuleEngine,
    "faker": FakerEngine,
}


def create_engine(engine_type: str, config_dict: Optional[Dict[str, Any]] = None) -> BaseEngine:
    engine_class = ENGINE_REGISTRY.get(str(engine_type).lower())
    if engine_class is None:
        print(f"EngineRegistry: Unknown engine_type '{engine_type}', using NullEngine fallback.")
        return NullEngine(config_dict)
    return engine_class(copy.deepcopy(config_dict or {}))
