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

    NEGATIVE_WORDS = {
        "weak", "poor", "bad", "lacking",
        "limited", "no", "not", "without",
        "inexperienced"
    }

    EMPLOYMENT_KEYWORDS = {
        "worked", "working", "employed", "joined",
        "intern", "experience", "company", "organization",
        "at", "with"
    }

    with open("src/resources/countries.json", "r", encoding="utf-8") as f:
        country_state_data = json.load(f)
    
    COUNTRY_SET = {
        country.strip().lower()
        for country in country_state_data.keys()
    }

    STATE_SET = {
        state.strip().lower()
        for states in country_state_data.values()
        for state in states
    }

    KNOWN_COMPANIES = {
        "google",
        "microsoft",
        "amazon",
        "meta",
        "apple",
        "infosys",
        "tcs",
        "wipro",
    }

    def __init__(
        self,
        notes_path: str,
        skills_path: str = "src/resources/skills.json",
        jobs_path: str = "src/resources/jobs.json",
    ):
        self.notes_path = notes_path
        self.skills_path = skills_path
        self.jobs_path = jobs_path

        self.skill_dictionary = self.load_skill_dictionary()
        self.jobs_dictionary = self.load_job_dictionary()

        # alias -> canonical skill
        self.skill_lookup = {}
        for canonical, aliases in self.skill_dictionary.items():
            self.skill_lookup[canonical.lower()] = canonical

            for alias in aliases:
                self.skill_lookup[alias.lower()] = canonical
        
        self.job_lookup = {}
        for canonical, aliases in self.jobs_dictionary.items():
            self.job_lookup[canonical.lower()] = canonical

            for alias in aliases:
                self.job_lookup[alias.lower()] = canonical

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
        
    def load_job_dictionary(self) -> Dict[str, List[str]]:
        with open(self.jobs_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =====================================================
    # Main Parser
    # =====================================================

    def parse(self) -> Candidate:

        text = self.load_notes()
        doc = self.nlp(text)

        candidate = Candidate()

        candidate.emails = self.extract_emails(text)
        candidate.phones = self.extract_phones(candidate, text)
        candidate.skills = self.extract_skills(doc)

        candidate.links = self.extract_links(text)

        candidate.full_name = self.extract_name(doc)
        candidate.location = self.extract_location(doc)

        companies = self.extract_companies(doc)
        roles = self.extract_job(doc)

        if companies:
            exp = Experience()
            exp.company = companies[0]
            exp.role = roles[0] if roles else None
            candidate.experience.append(exp)

        return candidate

    # =====================================================
    # General Normalization
    # =====================================================

    def normalize_value(self, value):

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

    # =====================================================
    # Name
    # =====================================================

    def extract_name(self, doc):

        for ent in doc.ents:

            if ent.label_ == "PERSON":
                return ent.text.strip()

        return None

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

    def extract_phones(self, candidate: Candidate, text: str) -> List[str]:

        phones = set()

        for phone in self.PHONE_REGEX.findall(text):

            normalized = self.normalize_phone(phone)

            if normalized and normalized not in candidate.phones:
                phones.add(normalized)

        return sorted(phones)

    # =====================================================
    # Skills
    # =====================================================

    def extract_skills(self, doc):

        found = set()

        for sent in doc.sents:

            clauses = re.split(r"\bbut\b|\bhowever\b|\byet\b|\balthough\b", sent.text, flags=re.I)

            for clause in clauses:

                clause_lower = clause.lower()

                for alias, canonical in self.skill_lookup.items():

                    if re.search(r"\b" + re.escape(alias) + r"\b", clause_lower):

                        if not any(neg in clause_lower for neg in self.NEGATIVE_WORDS):
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
    # Extract Companies
    # =====================================================

    def extract_companies(self, doc):

        companies = []
        seen = set()

        text_lower = doc.text.lower()

        for company in self.KNOWN_COMPANIES:
            if company in text_lower:
                companies.append(company.title())
                seen.add(company)

        for ent in doc.ents:

            if ent.label_ != "ORG":
                continue

            company = ent.text.strip()
            low = company.lower()

            # skip if already found
            if low in seen:
                continue

            if low in self.skill_lookup:
                continue

            companies.append(company)
            seen.add(low)

        return companies

    # =====================================================
    # Extract location
    # =====================================================

    def extract_location(self, doc):

        location = {
            "city": None,
            "state": None,
            "country": None,
        }

        for ent in doc.ents:

            if ent.label_ not in ("GPE", "LOC"):
                continue

            val = ent.text.strip()

            low = val.lower()

            if low in self.COUNTRY_SET:
                if location["country"] is None:
                    location["country"] = val

            elif low in self.STATE_SET:
                if location["state"] is None:
                    location["state"] = val

            else:
                if location["city"] is None:
                    location["city"] = val

        return location
    
    # =====================================================
    # Extract Job
    # =====================================================

    def extract_job(self, doc):

        roles = []
        seen = set()

        text_lower = doc.text.lower()

        for alias, canonical in self.job_lookup.items():

            if alias in text_lower:

                if canonical.lower() not in seen:
                    roles.append(canonical)
                    seen.add(canonical.lower())

        return roles