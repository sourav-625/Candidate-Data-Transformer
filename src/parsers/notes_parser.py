import json
import re
from typing import Dict, List, Optional

import spacy

from src.models.candidate import Candidate, Experience


class NotesParser:
    """
    Parses an unstructured recruiter notes text file into a canonical
    Candidate object.
    """

    EMAIL_REGEX = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    PHONE_REGEX = re.compile(
        r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{5}[\s-]?\d{5}"
    )

    GITHUB_REGEX = re.compile(
        r"https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )

    LINKEDIN_REGEX = re.compile(
        r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )

    URL_REGEX = re.compile(
        r"https?://[^\s]+",
        re.IGNORECASE,
    )

    def __init__(
        self,
        notes_path: str,
        skills_path: str,
    ):
        self.notes_path = notes_path
        self.skills_path = skills_path

        self.skill_dictionary = self.load_skill_dictionary()

        # alias -> canonical skill
        self.skill_lookup = {}
        for canonical, aliases in self.skill_dictionary.items():
            self.skill_lookup[canonical.lower()] = canonical

            for alias in aliases:
                self.skill_lookup[alias.lower()] = canonical

        self.nlp = spacy.load("en_core_web_sm")

    # =====================================================
    # File Loading
    # =====================================================

    def load_notes(self) -> str:
        with open(self.notes_path, "r", encoding="utf-8") as f:
            return f.read()

    def load_skill_dictionary(self) -> Dict[str, List[str]]:
        with open(self.skills_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =====================================================
    # Main Parser
    # =====================================================

    def parse(self) -> Candidate:

        text = self.load_notes()
        doc = self.nlp(text)

        candidate = Candidate()

        candidate.emails = self.extract_emails(text)
        candidate.phones = self.extract_phones(text)
        candidate.skills = self.extract_skills(text)

        candidate.links = self.extract_links(text)

        entities = self.extract_entities(doc)

        candidate.full_name = entities["name"]
        candidate.location = entities["location"]

        if entities["companies"]:
            exp = Experience()
            exp.company = entities["companies"][0]
            candidate.experience.append(exp)

        return candidate

    # =====================================================
    # Email
    # =====================================================

    def extract_emails(self, text: str) -> List[str]:

        emails = {
            email.strip().lower()
            for email in self.EMAIL_REGEX.findall(text)
        }

        return sorted(emails)

    # =====================================================
    # Phone
    # =====================================================

    def normalize_phone(self, phone: str) -> str:

        digits = re.sub(r"[^\d+]", "", phone)

        return digits

    def extract_phones(self, text: str) -> List[str]:

        phones = set()

        for phone in self.PHONE_REGEX.findall(text):

            normalized = self.normalize_phone(phone)

            if normalized:
                phones.add(normalized)

        return sorted(phones)

    # =====================================================
    # Skills
    # =====================================================

    def extract_skills(self, text: str) -> List[str]:

        text_lower = text.lower()

        found = set()

        for alias, canonical in self.skill_lookup.items():

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text_lower):
                found.add(canonical)

        return sorted(found)

    # =====================================================
    # Links
    # =====================================================

    def extract_links(
        self,
        text: str,
    ) -> Dict[str, Optional[str]]:

        links = {
            "github": None,
            "linkedin": None,
            "portfolio": None,
        }

        github = self.GITHUB_REGEX.search(text)
        linkedin = self.LINKEDIN_REGEX.search(text)

        if github:
            links["github"] = github.group(0)

        if linkedin:
            links["linkedin"] = linkedin.group(0)

        urls = self.URL_REGEX.findall(text)

        for url in urls:

            lower = url.lower()

            if "github.com" in lower:
                continue

            if "linkedin.com" in lower:
                continue

            links["portfolio"] = url
            break

        return links

    # =====================================================
    # Named Entity Recognition
    # =====================================================

    def extract_entities(
        self,
        doc,
    ) -> Dict:

        name = None

        companies = []

        location = {
            "city": None,
            "state": None,
            "country": None,
        }

        seen_companies = set()

        for ent in doc.ents:

            if ent.label_ == "PERSON":

                if name is None:
                    name = ent.text.strip()

            elif ent.label_ == "ORG":

                company = ent.text.strip()

                if company.lower() not in seen_companies:
                    companies.append(company)
                    seen_companies.add(company.lower())

            elif ent.label_ in ("GPE", "LOC"):

                if location["city"] is None:
                    location["city"] = ent.text.strip()

        return {
            "name": name,
            "companies": companies,
            "location": location,
        }