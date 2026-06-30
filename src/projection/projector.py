import json
import re
from typing import Any, Dict

from src.models.candidate import Candidate


class Projector:
    """
    Projects a canonical Candidate object into a runtime-defined
    output schema.
    """

    def __init__(self, config_path: str):

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    # --------------------------------------------------------

    def get_nested_value(
        self,
        candidate: Candidate,
        path: str
    ) -> Any:

        current = candidate

        parts = path.split(".")

        for part in parts:

            match = re.match(r"(\w+)\[(\d+)\]", part)

            if match:

                name = match.group(1)
                index = int(match.group(2))

                current = getattr(current, name)

                if index >= len(current):
                    return None

                current = current[index]

            else:

                if isinstance(current, dict):
                    current = current.get(part)

                else:
                    current = getattr(current, part)

            if current is None:
                return None

        return current

    # --------------------------------------------------------

    def apply_missing_strategy(
        self,
        output: Dict,
        key: str,
        value: Any,
    ):

        strategy = self.config.get(
            "missing",
            "null"
        )

        if value is not None:

            output[key] = value

            return

        if strategy == "null":

            output[key] = None

        elif strategy == "omit":

            return

        elif strategy == "error":

            raise ValueError(
                f"Missing required field: {key}"
            )

    # --------------------------------------------------------

    def serialize(self, value: Any) -> Any:
        """
        Recursively convert custom objects into JSON-serializable
        Python types (dict, list, str, int, float, bool, None).
        """

        if value is None:
            return None

        # Primitive types
        if isinstance(value, (str, int, float, bool)):
            return value

        # Lists
        if isinstance(value, list):
            return [self.serialize(item) for item in value]

        # Dictionaries
        if isinstance(value, dict):
            return {
                key: self.serialize(val)
                for key, val in value.items()
            }

        # Custom classes (Experience, Education, etc.)
        if hasattr(value, "__dict__"):
            return {
                key: self.serialize(val)
                for key, val in value.__dict__.items()
            }

        # Fallback
        return str(value)

    def project(
        self,
        candidate: Candidate
    ) -> Dict:

        output = {}

        fields = self.config.get(
            "fields",
            {}
        )

        for out_field, candidate_path in fields.items():

            value = self.serialize(
                self.get_nested_value(
                    candidate,
                    candidate_path
                )
            )

            self.apply_missing_strategy(
                output,
                out_field,
                value
            )

        if self.config.get(
            "include_confidence",
            False
        ):
            output["overall_confidence"] = (
                candidate.overall_confidence
            )

        if self.config.get(
            "include_provenance",
            False
        ):
            output["provenance"] = self.serialize(
                candidate.provenance
            )

        return output