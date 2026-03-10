import copy
import random
import re
from typing import Any, Dict, List, Optional, Type


class BaseEngine:
    """Common contract for all factory engines."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config_dict = config_dict or {}

    def process(self, payload: Any, instructions: Dict[str, Any]) -> Any:
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
        rules = instructions.get("rules", [])
        default_state = int(instructions.get("default_state", 0))

        if not isinstance(rules, list):
            return "fatal: regex instructions.rules must be a list"

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            pattern = str(rule.get("pattern", ""))
            state = int(rule.get("state", default_state))

            if isinstance(payload, dict):
                target_field = rule.get("target_field")
                if not target_field:
                    return "fatal: missing target_field for dictionary payload"
                candidate_value = payload.get(str(target_field), "")
            else:
                candidate_value = payload

            candidate_text = "" if candidate_value is None else str(candidate_value)

            try:
                if re.search(pattern, candidate_text):
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


ENGINE_REGISTRY: Dict[str, Type[BaseEngine]] = {
    "regex": RegexEngine,
    "random": RandomEngine,
}


def create_engine(engine_type: str, config_dict: Optional[Dict[str, Any]] = None) -> BaseEngine:
    engine_class = ENGINE_REGISTRY.get(str(engine_type).lower())
    if engine_class is None:
        print(f"EngineRegistry: Unknown engine_type '{engine_type}', using NullEngine fallback.")
        return NullEngine(config_dict)
    return engine_class(copy.deepcopy(config_dict or {}))
