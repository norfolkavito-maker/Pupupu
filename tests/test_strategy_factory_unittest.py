import unittest

from zapret_manager.strategies.model import StrategyFactory


class StrategyFactoryTests(unittest.TestCase):
    def test_create_game_strategy_without_args_key(self):
        st = StrategyFactory.create_game_strategy("Gv1")
        self.assertEqual(st.kind, "game")
        self.assertTrue(any(a.startswith("--wf-udp=") for a in st.args))

    def test_create_discord_strategy_without_args_key(self):
        st = StrategyFactory.create_discord_strategy("Dv1")
        self.assertEqual(st.kind, "discord")
        self.assertTrue(any(a.startswith("--block=") for a in st.args))

    def test_create_youtube_strategy_without_args_key(self):
        st = StrategyFactory.create_youtube_strategy("Yv1")
        self.assertEqual(st.kind, "youtube")
        self.assertTrue(any(a.startswith("--hostlist=") for a in st.args))


if __name__ == "__main__":
    unittest.main()