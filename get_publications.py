# pyright: basic, reportExplicitAny=false

import csv
import json
from typing import Any

from jsonschema import Draft7Validator

CSV_FILE = "./publications_2026.csv"
JSON_FILE = "./publications.json"
SCHEMA_PATH = "./schema.json"


class PublicationConverter:
    def __init__(self, csv_path: str, schema_path: str | None = None):
        self.csv_path: str = csv_path
        self.rows: list[dict[str, str]] = []
        self.publications: list[dict[str, Any]] = []
        self.schema: dict[str, Any] | None = None

        if schema_path:
            self.load_schema(schema_path)

    # ----------------------------
    # Schema
    # ----------------------------
    def load_schema(self, schema_path: str) -> None:
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.validator = Draft7Validator(
            self.schema  # pyright: ignore[reportArgumentType]
        )

    def validate_publications(self, raise_on_error: bool = True) -> list[str]:
        if not self.schema:
            raise ValueError("Schema not loaded")

        errors = []
        for error in self.validator.iter_errors(self.publications):
            errors.append(error.message)

        if errors and raise_on_error:
            raise ValueError("Schema validation failed:\n" + "\n".join(errors))

        return errors

    # ----------------------------
    # Loading
    # ----------------------------
    def load_csv(self) -> None:
        with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self.rows = [row for row in reader]

    def load_json(self, json_path: str, validate_schema: bool = False) -> None:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON must be a list")

        self.publications = data

        if validate_schema:
            self.validate_publications()

    # ----------------------------
    # Core transformation helpers
    # ----------------------------
    def _parse_authors(self, authors_str: str) -> list[str]:
        if not authors_str:
            return []
        return [a.strip() for a in authors_str.split(",") if a.strip()]

    def _build_core_fields(self, row: dict[str, str]) -> dict[str, Any]:
        return {
            "title": row.get("title", ""),
            "category": row.get("item_type", ""),  # map item_type → category
            "sessionTime": "",  # placeholder (fill later if you have logic)
            "authors": self._parse_authors(row.get("authors", "")),
            "link": row.get("item_url", ""),
        }

    def _build_raw(self, row: dict[str, str]) -> dict[str, Any]:
        # Keep EVERYTHING exactly as-is
        return dict(row)

    # ----------------------------
    # Conversion
    # ----------------------------
    def convert(self, validate_schema: bool = True) -> list[dict[str, Any]]:
        if not self.rows:
            self.load_csv()

        self.publications = []

        for row in self.rows:
            publication = self._build_core_fields(row)
            publication["raw"] = self._build_raw(row)
            self.publications.append(publication)

        if validate_schema:
            self.validate_publications()

        return self.publications

    # ----------------------------
    # Export
    # ----------------------------
    def to_json(self, output_path: str, indent: int = 2) -> None:
        if not self.publications:
            self.convert()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.publications, f, indent=indent, ensure_ascii=True)

    # ----------------------------
    # Analysis / Summary functions
    # ----------------------------
    def count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for pub in self.publications:
            cat = pub.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1

        return counts

    def count_authors(self) -> int:
        unique_authors = set()

        for pub in self.publications:
            for author in pub.get("authors", []):
                unique_authors.add(author)

        return len(unique_authors)

    def filter_by_category(self, category: str) -> list[dict[str, Any]]:
        return [p for p in self.publications if p.get("category") == category]

    def get_award_winners(self) -> list[dict[str, Any]]:
        winners = []

        for pub in self.publications:
            raw = pub.get("raw", {})
            award = raw.get("Awards")

            if award and award.strip():
                winners.append(pub)

        return winners

    def search_title(self, keyword: str) -> list[dict[str, Any]]:
        keyword = keyword.lower()
        return [p for p in self.publications if keyword in p.get("title", "").lower()]


def main():
    converter = PublicationConverter(CSV_FILE, SCHEMA_PATH)

    # Convert
    # converter.convert()

    # Save JSON
    # converter.to_json(JSON_FILE)

    # Load JSON
    converter.load_json(JSON_FILE)

    # Summaries
    # print("By category:", converter.count_by_category())
    # print("Unique authors:", converter.count_authors())

    # Queries
    # papers = converter.filter_by_category("paper")
    # awards = converter.get_award_winners()
    # ai_papers = converter.search_title("AI")


if __name__ == "__main__":
    main()
