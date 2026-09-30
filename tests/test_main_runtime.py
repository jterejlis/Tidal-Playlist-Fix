import unittest

import main


class MainRuntimeTests(unittest.TestCase):
    def test_tidal_search_is_available(self):
        self.assertTrue(hasattr(main, "tidal_search"))
        self.assertTrue(callable(main.tidal_search))


if __name__ == "__main__":
    unittest.main()
