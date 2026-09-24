import unittest


class ImportTest(unittest.TestCase):
    def test_core_modules_import(self):
        from src import (
            backtest,
            data,
            harness,
            indicators,
            mcp_server,
            news_aliases,
            news_context,
            research,
            rss_news,
        )

        self.assertIsNotNone(backtest)
        self.assertIsNotNone(data)
        self.assertIsNotNone(harness)
        self.assertIsNotNone(indicators)
        self.assertIsNotNone(mcp_server)
        self.assertIsNotNone(news_aliases)
        self.assertIsNotNone(news_context)
        self.assertIsNotNone(research)
        self.assertIsNotNone(rss_news)


if __name__ == "__main__":
    unittest.main()
