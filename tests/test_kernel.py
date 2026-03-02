"""Test kernel diagnostics"""

import unittest
from unittest.mock import patch, mock_open
from diag.kernel import check_kernel_taint, check_dmesg_errors, check_oom_kills

class TestKernelTaint(unittest.TestCase):
    
    @patch('builtins.open', mock_open(read_data='0\n'))
    def test_clean_kernel(self):
        findings = check_kernel_taint()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'OK')
    
    @patch('builtins.open', mock_open(read_data='4096\n'))
    def test_tainted_kernel(self):
        findings = check_kernel_taint()
        self.assertEqual(findings[0]['severity'], 'WARNING')
        self.assertIn('tainted', findings[0]['issue'].lower())
    
    @patch('builtins.open', mock_open(read_data='1\n'))
    def test_proprietary_module(self):
        findings = check_kernel_taint()
        self.assertEqual(findings[0]['severity'], 'WARNING')
        self.assertIn('Proprietary', findings[0]['issue'])

class TestDmesgErrors(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_no_errors(self, mock_run):
        mock_run.return_value.stdout = ''
        mock_run.return_value.returncode = 0
        findings = check_dmesg_errors()
        self.assertEqual(findings[0]['severity'], 'OK')
    
    @patch('subprocess.run')
    def test_hardware_errors(self, mock_run):
        mock_run.return_value.stdout = '[1234.56] hardware error detected\n'
        mock_run.return_value.returncode = 0
        findings = check_dmesg_errors()
        has_critical = any(f['severity'] == 'CRITICAL' for f in findings)
        self.assertTrue(has_critical)
    
    @patch('subprocess.run')
    def test_io_errors(self, mock_run):
        mock_run.return_value.stdout = '[1234.56] I/O error on device sda\n'
        mock_run.return_value.returncode = 0
        findings = check_dmesg_errors()
        has_critical = any(f['severity'] == 'CRITICAL' for f in findings)
        self.assertTrue(has_critical)

class TestOOMKills(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_oom_detected(self, mock_run):
        mock_run.return_value.stdout = '[1234.56] Out of memory: Killed process 123\n'
        mock_run.return_value.returncode = 0
        findings = check_oom_kills()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'CRITICAL')
    
    @patch('subprocess.run')
    def test_no_oom(self, mock_run):
        mock_run.return_value.stdout = '[1234.56] normal kernel message\n'
        mock_run.return_value.returncode = 0
        findings = check_oom_kills()
        self.assertEqual(len(findings), 0)

if __name__ == '__main__':
    unittest.main()
