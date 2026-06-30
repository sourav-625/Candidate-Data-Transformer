import argparse
import json
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

    args = parser.parse_args()

    pipeline = Pipeline()

    pipeline.run(
        csv_path=args.csv,
        notes_path=args.notes,
        config_path=args.config,
        output_path=args.output,
    )

    print(f"Output written to {args.output}")

    with open(args.output, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()