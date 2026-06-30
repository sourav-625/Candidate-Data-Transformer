from typing import Any, Dict, List, Tuple


class ConflictResolver:
    """
    Generic conflict resolution utilities.

    This class only knows HOW to merge values.
    It has no knowledge of Candidate objects.
    """

    # ==========================================================
    # Helper Functions
    # ==========================================================

    @staticmethod
    def is_empty(value: Any) -> bool:
        """Return True if a value should be treated as empty."""

        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() == ""

        if isinstance(value, (list, dict, tuple, set)):
            return len(value) == 0

        return False

    @staticmethod
    def normalize_value(value: Any) -> str:
        """Normalize values before comparison."""

        if value is None:
            return ""

        return str(value).strip().lower()

    @classmethod
    def values_equal(cls, first: Any, second: Any) -> bool:
        """
        Compare two values after normalization.
        """

        if cls.is_empty(first) and cls.is_empty(second):
            return True

        if cls.is_empty(first) or cls.is_empty(second):
            return False

        return cls.normalize_value(first) == cls.normalize_value(second)

    @staticmethod
    def build_provenance(
        sources: List[str],
        strategy: str
    ) -> Dict[str, Any]:
        return {
            "sources": sources,
            "strategy": strategy
        }

    # ==========================================================
    # Scalar Merge
    # ==========================================================

    @classmethod
    def merge_scalar(
        cls,
        primary: Any,
        secondary: Any,
        primary_source: str = "csv",
        secondary_source: str = "notes",
        strategy: str = "prefer_primary"
    ) -> Tuple[Any, Dict]:

        p_empty = cls.is_empty(primary)
        s_empty = cls.is_empty(secondary)

        # both missing
        if p_empty and s_empty:
            return None, cls.build_provenance([], strategy)

        # only primary
        if not p_empty and s_empty:
            return primary, cls.build_provenance(
                [primary_source],
                strategy
            )

        # only secondary
        if p_empty and not s_empty:
            return secondary, cls.build_provenance(
                [secondary_source],
                strategy
            )

        # both equal
        if cls.values_equal(primary, secondary):
            return primary, cls.build_provenance(
                [primary_source, secondary_source],
                "agreement"
            )

        # conflict
        if strategy == "null_on_conflict":
            return None, cls.build_provenance(
                [primary_source, secondary_source],
                "null_on_conflict"
            )

        # default
        return primary, cls.build_provenance(
            [primary_source],
            "prefer_primary"
        )

    # ==========================================================
    # List Merge
    # ==========================================================

    @classmethod
    def merge_list(
        cls,
        primary: List[Any],
        secondary: List[Any],
        primary_source: str = "csv",
        secondary_source: str = "notes",
        strategy: str = "union"
    ) -> Tuple[List[Any], Dict]:

        merged = []
        seen = set()

        for item in (primary or []) + (secondary or []):

            key = cls.normalize_value(item)

            if key not in seen:
                seen.add(key)
                merged.append(item)

        sources = []

        if not cls.is_empty(primary):
            sources.append(primary_source)

        if not cls.is_empty(secondary):
            sources.append(secondary_source)

        return merged, cls.build_provenance(
            sources,
            strategy
        )

    # ==========================================================
    # Dictionary Merge
    # ==========================================================

    @classmethod
    def merge_dict(
        cls,
        primary: Dict[str, Any],
        secondary: Dict[str, Any],
        primary_source: str = "csv",
        secondary_source: str = "notes",
        strategy: str = "null_on_conflict"
    ) -> Tuple[Dict[str, Any], Dict]:

        merged = {}

        all_keys = set(primary.keys()) | set(secondary.keys())

        for key in all_keys:

            p = primary.get(key)
            s = secondary.get(key)

            p_empty = cls.is_empty(p)
            s_empty = cls.is_empty(s)

            # both missing
            if p_empty and s_empty:
                merged[key] = None

            # only primary
            elif not p_empty and s_empty:
                merged[key] = p

            # only secondary
            elif p_empty and not s_empty:
                merged[key] = s

            # same value
            elif cls.values_equal(p, s):
                merged[key] = p

            # conflict
            elif strategy == "null_on_conflict":
                merged[key] = None

            else:
                merged[key] = p

        sources = []

        if not cls.is_empty(primary):
            sources.append(primary_source)

        if not cls.is_empty(secondary):
            sources.append(secondary_source)

        return merged, cls.build_provenance(
            sources,
            strategy
        )

    # ==========================================================
    # Object List Merge
    # ==========================================================

    @classmethod
    def merge_object_list(
        cls,
        primary: List[Any],
        secondary: List[Any],
        primary_source: str = "csv",
        secondary_source: str = "notes",
        strategy: str = "union"
    ) -> Tuple[List[Any], Dict]:

        merged = []
        seen = set()

        for obj in (primary or []) + (secondary or []):

            if hasattr(obj, "model_dump"):
                key = tuple(sorted(obj.model_dump().items()))

            elif isinstance(obj, dict):
                key = tuple(sorted(obj.items()))

            else:
                key = cls.normalize_value(obj)

            if key not in seen:
                seen.add(key)
                merged.append(obj)

        sources = []

        if not cls.is_empty(primary):
            sources.append(primary_source)

        if not cls.is_empty(secondary):
            sources.append(secondary_source)

        return merged, cls.build_provenance(
            sources,
            strategy
        )