import argparse

from src.pipeline import Pipeline


def main():

    parser = argparse.ArgumentParser(
        description="Multi-Source Candidate Data Transformer"
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Path to recruiter CSV"
    )

    parser.add_argument(
        "--notes",
        required=True,
        help="Path to recruiter notes"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Projection configuration JSON"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path"
    )

    parser.add_argument(
        "--skills",
        default="src/resources/skills.json",
        help="Skills dictionary"
    )

    args = parser.parse_args()

    pipeline = Pipeline()

    pipeline.run(
        csv_path=args.csv,
        notes_path=args.notes,
        skills_path=args.skills,
        config_path=args.config,
        output_path=args.output,
    )

    print(f"Output written to {args.output}")


if __name__ == "__main__":
    main()