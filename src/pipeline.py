import json
from pathlib import Path

from src.parsers.csv_parser import CSVParser
from src.parsers.notes_parser import NotesParser
from src.merging.merger import Merger
from src.validation.validator import Validator
from src.projection.projector import Projector


class Pipeline:
    """
    Orchestrates the complete candidate transformation pipeline.

    Pipeline Flow:
        CSV Parser
            ↓
        Notes Parser
            ↓
        Merge
            ↓
        Validate
            ↓
        Project
            ↓
        Save Output
    """

    def __init__(self):
        self.merger = Merger()
        self.validator = Validator()

    def run(
        self,
        csv_path: str,
        notes_path: str,
        config_path: str,
        output_path: str,
    ):
        # --------------------------------------------------
        # Parse Inputs
        # --------------------------------------------------

        print("[1/6] Parsing CSV...")

        csv_candidate = CSVParser(csv_path).load_candidates()

        print("[2/6] Parsing Recruiter Notes...")

        notes_candidate = NotesParser(
            notes_path,
        ).parse()

        # --------------------------------------------------
        # Merge
        # --------------------------------------------------

        print("[3/6] Merging Candidate Profiles...")

        merged_candidate = self.merger.merge(
            csv_candidate,
            notes_candidate,
        )

        # --------------------------------------------------
        # Validate
        # --------------------------------------------------

        print("[4/6] Validating Candidate...")

        validated_candidate, warnings = self.validator.validate(
            merged_candidate
        )

        # --------------------------------------------------
        # Projection
        # --------------------------------------------------

        print("[5/6] Applying Runtime Projection...")

        projector = Projector(config_path)

        output = projector.project(
            validated_candidate
        )

        # --------------------------------------------------
        # Save JSON
        # --------------------------------------------------

        print("[6/6] Writing Output...")

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                output,
                f,
                indent=4,
                ensure_ascii=False,
            )

        print("\nTransformation Complete!")

        if warnings:

            print("\nValidation Warnings:")

            for warning in warnings:
                print(f" - {warning}")

        else:
            print("\nNo validation warnings.")

        return output