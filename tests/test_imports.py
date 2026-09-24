import unittest


class ImportTest(unittest.TestCase):
    def test_core_modules_import(self):
        from src import (
            backtest,
            data,
            fundamentals_status,
            harness,
            indicators,
            macro_context_status,
            market_audit,
            mcp_server,
            news_aliases,
            news_context,
            research,
            rss_news,
            yfinance_fundamentals,
        )

        self.assertIsNotNone(backtest)
        self.assertIsNotNone(data)
        self.assertIsNotNone(fundamentals_status)
        self.assertIsNotNone(harness)
        self.assertIsNotNone(indicators)
        self.assertIsNotNone(macro_context_status)
        self.assertIsNotNone(market_audit)
        self.assertIsNotNone(mcp_server)
        self.assertIsNotNone(news_aliases)
        self.assertIsNotNone(news_context)
        self.assertIsNotNone(research)
        self.assertIsNotNone(rss_news)
        self.assertIsNotNone(yfinance_fundamentals)


if __name__ == "__main__":
    unittest.main()
