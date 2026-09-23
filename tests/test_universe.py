import csv
import unittest
from pathlib import Path

from src.data import REQUIRED_UNIVERSE_COLUMNS, load_universe, validate_universe


UNIVERSE_PATH = Path(__file__).resolve().parents[1] / "config" / "universe.csv"


class UniverseTest(unittest.TestCase):
    def test_universe_csv_has_required_columns(self):
        with UNIVERSE_PATH.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)

            self.assertEqual(list(REQUIRED_UNIVERSE_COLUMNS), reader.fieldnames)

    def test_universe_has_exactly_30_valid_members(self):
        members = load_universe(UNIVERSE_PATH)

        self.assertEqual([], validate_universe(members))
        self.assertEqual(30, len(members))

    def test_universe_tickers_are_unique(self):
        members = load_universe(UNIVERSE_PATH)
        tickers = [member.ticker for member in members]

        self.assertEqual(len(tickers), len(set(tickers)))


if __name__ == "__main__":
    unittest.main()
