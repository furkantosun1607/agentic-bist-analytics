import unittest


class ImportTest(unittest.TestCase):
    def test_core_modules_import(self):
        from src import (
            backtest,
            backtest_reports,
            data,
            fundamentals_status,
            harness,
            indicators,
            macro_context_fetch,
            macro_context_status,
            market_audit,
            mcp_server,
            news_aliases,
            news_context,
            research,
            research_reports,
            rss_news,
            split_regime_reports,
            strategy_variant_reports,
            yfinance_fundamentals,
        )

        self.assertIsNotNone(backtest)
        self.assertIsNotNone(backtest_reports)
        self.assertIsNotNone(data)
        self.assertIsNotNone(fundamentals_status)
        self.assertIsNotNone(harness)
        self.assertIsNotNone(indicators)
        self.assertIsNotNone(macro_context_fetch)
        self.assertIsNotNone(macro_context_status)
        self.assertIsNotNone(market_audit)
        self.assertIsNotNone(mcp_server)
        self.assertIsNotNone(news_aliases)
        self.assertIsNotNone(news_context)
        self.assertIsNotNone(research)
        self.assertIsNotNone(research_reports)
        self.assertIsNotNone(rss_news)
        self.assertIsNotNone(split_regime_reports)
        self.assertIsNotNone(strategy_variant_reports)
        self.assertIsNotNone(yfinance_fundamentals)


if __name__ == "__main__":
    unittest.main()
