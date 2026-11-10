import unittest

from discordrpc.exceptions import ProgressbarError
from discordrpc.utils import progress_bar


class ProgressBarTests(unittest.TestCase):
    def test_valid_progress(self):
        result = progress_bar(50, 200)
        self.assertIn("ts_start", result)
        self.assertIn("ts_end", result)
        self.assertLess(result["ts_start"], result["ts_end"])

    def test_current_equal_to_duration(self):
        result = progress_bar(200, 200)
        self.assertEqual(result["ts_end"] - result["ts_start"], 200)

    def test_negative_current_raises(self):
        with self.assertRaises(ProgressbarError):
            progress_bar(-1, 200)

    def test_zero_duration_raises(self):
        with self.assertRaises(ProgressbarError):
            progress_bar(0, 0)

    def test_negative_duration_raises(self):
        with self.assertRaises(ProgressbarError):
            progress_bar(0, -5)

    def test_current_exceeds_duration_raises(self):
        with self.assertRaises(ProgressbarError):
            progress_bar(300, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
