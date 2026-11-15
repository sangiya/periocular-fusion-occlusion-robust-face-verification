"""Recovery retries must be bounded and must not hide scientific/code errors."""
import unittest
from unittest.mock import patch
from run_cpu_sweep import retryable_exit,verified_completed

class RecoveryGuards(unittest.TestCase):
    def test_observed_interruption_has_only_three_retries(self):
        for attempt in range(3):self.assertTrue(retryable_exit(0x40010004,attempt))
        self.assertFalse(retryable_exit(0x40010004,3))
    def test_code_errors_and_control_c_are_not_retried(self):
        for code in [1,2,0xC000013A,-1073741510]:self.assertFalse(retryable_exit(code,0))
    def test_no_report_is_not_a_completed_model(self):
        self.assertFalse(verified_completed(999999,'nonexistent_fixture'))

if __name__=='__main__':unittest.main()
