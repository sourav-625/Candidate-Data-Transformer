import re
from typing import List, Dict, Optional

import spacy

from src.models.candidate import Candidate, Education, Experience

class NotesAdapter:
    def __init__(self, skill_dictionary: List[str]):
        self.skill_set = set([s.lower() for s in skill_dictionary])

        # Load spaCy model once
        self.nlp = spacy.load("en_core_web_sm")

    # ----------------------------
    # MAIN PIPELINE
    # ----------------------------
    def parse(self, text: str) -> Candidate:
        doc = self.nlp(text)

        candidate = Candidate()
        exp = Experience()

        candidate.emails = self.extract_emails(text)
        candidate.phones = self.extract_phones(text)
        candidate.skills = self.extract_skills(text)

        candidate.full_name = self.extract_name(doc)
        candidate.location = self.extract_location(doc)
        candidate.links = self.extract_links(text)
        exp.company = self.extract_company(doc)

        return candidate

    # ----------------------------
    # EMAIL
    # ----------------------------
    def extract_emails(self, text: str) -> List[str]:
        pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        return list(set(re.findall(pattern, text)))

    # ----------------------------
    # PHONE
    # ----------------------------
    def extract_phones(self, text: str) -> List[str]:
        pattern = r"\b\d{10}\b"
        return list(set(re.findall(pattern, text)))

    # ----------------------------
    # SKILLS (dictionary-based)
    # ----------------------------
    def extract_skills(self, text: str) -> List[str]:
        words = re.findall(r"[a-zA-Z]+", text.lower())

        skills = set()
        for w in words:
            if w in self.skill_set:
                skills.add(w.capitalize())

        return list(skills)

    # ----------------------------
    # NAME (spaCy PERSON)
    # ----------------------------
    def extract_name(self, doc) -> Optional[str]:
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return None

    # ----------------------------
    # LOCATION (spaCy GPE / LOC)
    # ----------------------------
    def extract_location(self, doc) -> Dict[str, Optional[str]]:
        location = {
            "city": None,
            "state": None,
            "country": None
        }

        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                # naive assignment strategy (can be improved later)
                if location["city"] is None:
                    location["city"] = ent.text
                elif location["state"] is None:
                    location["state"] = ent.text
                elif location["country"] is None:
                    location["country"] = ent.text

        return location

    # ----------------------------
    # COMPANY (spaCy ORG)
    # ----------------------------
    def extract_company(self, doc) -> List[str]:
        companies = set()

        for ent in doc.ents:
            if ent.label_ == "ORG":
                companies.add(ent.text)

        return list(companies)

    # ----------------------------
    # OPTIONAL: LINKS (future extension)
    # ----------------------------
    def extract_links(self, text: str) -> Dict[str, Optional[str]]:
        links = {
            "github": None,
            "linkedin": None,
            "portfolio": None
        }

        github = re.findall(r"github\.com/\S+", text)
        linkedin = re.findall(r"linkedin\.com/\S+", text)

        if github:
            links["github"] = github[0]

        if linkedin:
            links["linkedin"] = linkedin[0]

        return links