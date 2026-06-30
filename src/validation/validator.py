import re
from typing import List, Tuple

from src.models.candidate import Candidate


class Validator:
    """
    Validates a merged Candidate object.

    The validator performs only structural validation.
    It never invents or merges data.
    """

    EMAIL_REGEX = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    PHONE_REGEX = re.compile(
        r"^\+?\d{10,15}$"
    )

    REQUIRED_LOCATION_KEYS = (
        "city",
        "state",
        "country",
    )

    def validate(
        self,
        candidate: Candidate,
    ) -> Tuple[Candidate, List[str]]:

        warnings = []

        # ==========================================
        # Required fields
        # ==========================================

        if not candidate.candidate_id:
            warnings.append("Missing candidate_id.")

        if not candidate.full_name:
            warnings.append("Missing full_name.")

        # ==========================================
        # Emails
        # ==========================================

        valid_emails = []

        for email in candidate.emails:

            if self.EMAIL_REGEX.fullmatch(email):
                valid_emails.append(email)

            else:
                warnings.append(
                    f"Invalid email removed: {email}"
                )

        candidate.emails = valid_emails

        # ==========================================
        # Phones
        # ==========================================

        valid_phones = []

        for phone in candidate.phones:

            if self.PHONE_REGEX.fullmatch(phone):
                valid_phones.append(phone)

            else:
                warnings.append(
                    f"Invalid phone removed: {phone}"
                )

        candidate.phones = valid_phones

        # ==========================================
        # Confidence
        # ==========================================

        if (
            candidate.overall_confidence < 0
            or
            candidate.overall_confidence > 1
        ):
            warnings.append(
                "Overall confidence out of range. Reset to 0.0."
            )

            candidate.overall_confidence = 0.0

        # ==========================================
        # Location
        # ==========================================

        if candidate.location is None:
            candidate.location = {}

        for key in self.REQUIRED_LOCATION_KEYS:

            candidate.location.setdefault(key, None)

        return candidate, warnings