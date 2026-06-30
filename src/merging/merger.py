from src.models.candidate import Candidate
from src.merging.conflict_resolver import ConflictResolver
from src.merging.confidence import ConfidenceCalculator


class Merger:
    """
    Merges two Candidate objects into a single canonical profile.

    The merger delegates all conflict resolution to ConflictResolver
    and all confidence computation to ConfidenceCalculator.
    """

    MERGE_POLICIES = {

        # -------------------------
        # Scalars
        # -------------------------
        "candidate_id": ("scalar", "prefer_primary"),
        "full_name": ("scalar", "prefer_primary"),
        "headline": ("scalar", "prefer_primary"),
        "years_experience": ("scalar", "null_on_conflict"),

        # -------------------------
        # Lists
        # -------------------------
        "emails": ("list", "union"),
        "phones": ("list", "union"),
        "skills": ("list", "union"),

        # -------------------------
        # Dictionaries
        # -------------------------
        "location": ("dict", "null_on_conflict"),
        "links": ("dict", "null_on_conflict"),

        # -------------------------
        # Object Lists
        # -------------------------
        "experience": ("object_list", "union"),
        "education": ("object_list", "union"),
    }

    def __init__(self):

        self.resolver = ConflictResolver()
        self.confidence = ConfidenceCalculator()

    def merge(
        self,
        csv_candidate: Candidate,
        notes_candidate: Candidate
    ) -> Candidate:

        merged = Candidate()

        merge_methods = {
            "scalar": self.resolver.merge_scalar,
            "list": self.resolver.merge_list,
            "dict": self.resolver.merge_dict,
            "object_list": self.resolver.merge_object_list,
        }

        for field, (merge_type, strategy) in self.MERGE_POLICIES.items():

            merge_function = merge_methods[merge_type]

            value, provenance = merge_function(
                getattr(csv_candidate, field),
                getattr(notes_candidate, field),
                primary_source="csv",
                secondary_source="notes",
                strategy=strategy,
            )

            setattr(merged, field, value)
            merged.provenance[field] = provenance

        merged.overall_confidence = self.confidence.calculate(
            merged.provenance
        )

        return merged