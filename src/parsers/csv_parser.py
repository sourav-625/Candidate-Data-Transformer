import csv
import json
from typing import List, Dict, Any

from src.models.candidate import Candidate


class CSVParser:
    def __init__(self, csv_path: str, mapping_path: str = "src/resources/field_mapping.json"):
        self.csv_path = csv_path
        self.mapping_path = mapping_path
        self.field_mapping = self.load_field_mapping()

    # ----------------------------
    # Load mapping JSON
    # ----------------------------
    def load_field_mapping(self) -> Dict[str, str]:
        with open(self.mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        # normalize keys for safe lookup
        return {k.lower().strip(): v for k, v in mapping.items()}

    # ----------------------------
    # Normalize column names
    # ----------------------------
    def normalize_column_name(self, name: str) -> str:
        return name.lower().strip()

    # ----------------------------
    # Map single CSV row → Candidate
    # ----------------------------
    def map_record(self, row: Dict[str, Any]) -> Candidate:
        candidate = Candidate()

        for raw_col, value in row.items():
            if value is None or str(value).strip() == "":
                continue

            col = self.normalize_column_name(raw_col)

            if col not in self.field_mapping:
                continue  # ignore unknown columns safely

            field = self.field_mapping[col]

            # ----------------------------
            # Handle simple fields
            # ----------------------------
            if field == "full_name":
                candidate.full_name = value.strip()
            
            elif field == "candidate_id":
                candidate.candidate_id = value.strip()

            elif field == "emails":
                candidate.emails.append(value.strip())

            elif field == "phones":
                candidate.phones.append(value.strip())

            elif field == "skills":
                # split comma-separated skills
                skills = [s.strip() for s in value.split(",") if s.strip()]
                candidate.skills.extend(skills)

            elif field == "headline":
                candidate.headline = value.strip()

            elif field == "years_experience":
                try:
                    candidate.years_experience = float(value)
                except:
                    pass

            elif field == "city":
                candidate.location["city"] = value.strip()

            elif field == "state":
                candidate.location["state"] = value.strip()

            elif field == "country":
                candidate.location["country"] = value.strip()

            elif field == "github":
                candidate.links["github"] = value.strip()

            elif field == "linkedin":
                candidate.links["linkedin"] = value.strip()

            elif field == "portfolio":
                candidate.links["portfolio"] = value.strip()

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