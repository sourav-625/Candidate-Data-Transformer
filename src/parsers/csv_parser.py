import csv
import json
import re

from typing import List, Dict, Any

from src.models.candidate import Candidate


class CSVParser:
    def __init__(
        self,
        csv_path: str,
        mapping_path: str = "src/resources/field_mapping.json",
        skills_path: str = "src/resources/skills.json"
    ):

        self.csv_path = csv_path
        self.mapping_path = mapping_path
        self.skills_path = skills_path

        self.field_mapping = self.load_field_mapping()
        self.skill_dictionary = self.load_skill_dictionary()

        # Reverse lookup:
        # "python3" -> "Python"
        # "mysql" -> "SQL"
        self.skill_lookup = {}

        for canonical, aliases in self.skill_dictionary.items():

            self.skill_lookup[canonical.lower()] = canonical

            for alias in aliases:
                self.skill_lookup[alias.lower()] = canonical

    # ----------------------------
    # Load mapping JSON
    # ----------------------------
    def load_field_mapping(self) -> Dict[str, str]:
        with open(self.mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        # normalize keys for safe lookup
        return {k.lower().strip(): v for k, v in mapping.items()}
    
    # ----------------------------
    # Load skill dictionary
    # ----------------------------

    def load_skill_dictionary(self) -> Dict[str, List[str]]:

        with open(self.skills_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ----------------------------
    # Normalize column names
    # ----------------------------
    def normalize_column_name(self, name: str) -> str:
        return name.lower().strip()

    # ----------------------------
    # Generic value normalization
    # ----------------------------

    def normalize_value(self, value: Any):

        if value is None:
            return None

        value = str(value).strip()

        if value.lower() in {
            "",
            "na",
            "n/a",
            "none",
            "null",
            "-"
        }:
            return None

        return value


    # ----------------------------
    # Name
    # ----------------------------

    def normalize_name(self, name: str):

        name = self.normalize_value(name)

        if not name:
            return None

        return " ".join(name.split()).title()


    # ----------------------------
    # Email
    # ----------------------------

    def normalize_email(self, email: str):

        email = self.normalize_value(email)

        if not email:
            return None

        email = email.lower()

        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if re.fullmatch(pattern, email):
            return email

        return None


    # ----------------------------
    # Phone
    # ----------------------------

    def normalize_phone(self, phone: str):

        phone = self.normalize_value(phone)

        if not phone:
            return None

        # Keep only digits and +
        phone = re.sub(r"[^\d+]", "", phone)

        # If + appears somewhere other than the beginning,
        # remove all and prepend one later if needed.
        if phone.count("+") > 1 or ("+" in phone and not phone.startswith("+")):
            phone = "+" + re.sub(r"\+", "", phone)

        # Indian local numbers
        if re.fullmatch(r"\d{10}", phone):
            phone = "+91" + phone

        # Validate E.164-ish
        if re.fullmatch(r"\+\d{10,15}", phone):
            return phone

        return None

    # ----------------------------
    # Skills
    # ----------------------------

    def normalize_skills(self, skills: str):

        skills = self.normalize_value(skills)

        if not skills:
            return []

        normalized = []

        for skill in re.split(r"[,;]", skills):

            skill = " ".join(skill.split()).strip().lower()

            if not skill:
                continue

            canonical = self.skill_lookup.get(
                skill,
                skill.title()
            )

            if canonical not in normalized:
                normalized.append(canonical)

        return normalized

    # ----------------------------
    # URL
    # ----------------------------

    def normalize_url(self, url: str):

        url = self.normalize_value(url)

        if not url:
            return None

        url = url.strip()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url.rstrip("/")


    # ----------------------------
    # Location
    # ----------------------------

    def normalize_location(self, value: str):

        value = self.normalize_value(value)

        if not value:
            return None

        return " ".join(value.split()).title()


    # ----------------------------
    # Experience
    # ----------------------------

    def normalize_experience(self, value):

        value = self.normalize_value(value)

        if not value:
            return None

        match = re.search(r"\d+(\.\d+)?", value)

        if match:
            return float(match.group())

        return None

    # ----------------------------
    # Map single CSV row → Candidate
    # ----------------------------
    def map_record(self, row: Dict[str, Any]) -> Candidate:
        candidate = Candidate()

        for raw_col, value in row.items():

            value = self.normalize_value(value)

            if value is None:
                continue

            col = self.normalize_column_name(raw_col)

            if col not in self.field_mapping:
                continue

            field = self.field_mapping[col]

            # ----------------------------
            # Simple Fields
            # ----------------------------

            if field == "full_name":

                candidate.full_name = self.normalize_name(value)

            elif field == "candidate_id":

                candidate.candidate_id = self.normalize_value(value)

            elif field == "headline":

                candidate.headline = self.normalize_value(value)

            elif field == "years_experience":

                candidate.years_experience = self.normalize_experience(value)

            # ----------------------------
            # Emails
            # ----------------------------

            elif field == "emails":

                email = self.normalize_email(value)

                if email and email not in candidate.emails:
                    candidate.emails.append(email)

            # ----------------------------
            # Phones
            # ----------------------------

            elif field == "phones":

                phone = self.normalize_phone(value)

                if phone and phone not in candidate.phones:
                    candidate.phones.append(phone)

            # ----------------------------
            # Skills
            # ----------------------------

            elif field == "skills":

                for skill in self.normalize_skills(value):

                    if skill not in candidate.skills:
                        candidate.skills.append(skill)

            # ----------------------------
            # Location
            # ----------------------------

            elif field == "city":

                candidate.location["city"] = self.normalize_location(value)

            elif field == "state":

                candidate.location["state"] = self.normalize_location(value)

            elif field == "country":

                candidate.location["country"] = self.normalize_location(value)

            # ----------------------------
            # Links
            # ----------------------------

            elif field == "github":

                candidate.links["github"] = self.normalize_url(value)

            elif field == "linkedin":

                candidate.links["linkedin"] = self.normalize_url(value)

            elif field == "portfolio":

                candidate.links["portfolio"] = self.normalize_url(value)

        return candidate

    # ----------------------------
    # Load full CSV → List[Candidate]
    # ----------------------------
    def load_candidates(self) -> List[Candidate]:
        candidates = []

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                candidate = self.map_record(row)
                candidates.append(candidate)

        return candidates[0]