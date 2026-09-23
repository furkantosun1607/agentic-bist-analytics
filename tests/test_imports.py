import unittest


class ImportTest(unittest.TestCase):
    def test_core_modules_import(self):
        from src import backtest, data, harness, indicators, mcp_server, research

        self.assertIsNotNone(backtest)
        self.assertIsNotNone(data)
        self.assertIsNotNone(harness)
        self.assertIsNotNone(indicators)
        self.assertIsNotNone(mcp_server)
        self.assertIsNotNone(research)


if __name__ == "__main__":
    unittest.main()
