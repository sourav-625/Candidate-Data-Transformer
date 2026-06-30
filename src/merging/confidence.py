from typing import Dict, Any


class ConfidenceCalculator:
    """
    Computes confidence scores from provenance information.

    Confidence is determined solely by the merge strategy recorded
    during conflict resolution.
    """

    STRATEGY_SCORES = {
        "agreement": 1.00,
        "union": 0.95,
        "prefer_primary": 0.85,
        "null_on_conflict": 0.00,
    }

    @classmethod
    def field_confidence(cls, provenance: Dict[str, Any]) -> float:
        """
        Return the confidence score for a single merged field.
        """

        if not provenance:
            return 0.0

        strategy = provenance.get("strategy")

        return cls.STRATEGY_SCORES.get(strategy, 0.0)

    @classmethod
    def calculate(cls, provenance: Dict[str, Dict[str, Any]]) -> float:
        """
        Compute the overall confidence of a merged candidate profile.
        """

        if not provenance:
            return 0.0

        scores = [
            cls.field_confidence(field_provenance)
            for field_provenance in provenance.values()
        ]

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 2)