"""Test storage diagnostics"""

import unittest
from unittest.mock import patch
from diag.storage import check_disk_usage, check_readonly_mounts

class TestDiskUsage(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_healthy_disk(self, mock_run):
        mock_run.return_value.stdout = (
            "Mounted on Use% Avail Type\n"
            "/          45%  500G  ext4\n"
        )
        mock_run.return_value.returncode = 0
        findings = check_disk_usage()
        self.assertEqual(findings[0]['severity'], 'OK')
    
    @patch('subprocess.run')
    def test_critical_disk(self, mock_run):
        mock_run.return_value.stdout = (
            "Mounted on Use% Avail Type\n"
            "/          97%  2G    ext4\n"
        )
        mock_run.return_value.returncode = 0
        findings = check_disk_usage()
        self.assertEqual(findings[0]['severity'], 'CRITICAL')
    
    @patch('subprocess.run')
    def test_warning_disk(self, mock_run):
        mock_run.return_value.stdout = (
            "Mounted on Use% Avail Type\n"
            "/          88%  50G   ext4\n"
        )
        mock_run.return_value.returncode = 0
        findings = check_disk_usage()
        self.assertEqual(findings[0]['severity'], 'WARNING')
    
    @patch('subprocess.run')
    def test_snap_mounts_skipped(self, mock_run):
        mock_run.return_value.stdout = (
            "Mounted on           Use% Avail Type\n"
            "/snap/core22/1234    100% 0     squashfs\n"
        )
        mock_run.return_value.returncode = 0
        findings = check_disk_usage()
        # Snap should be skipped, no findings
        self.assertEqual(len(findings), 0)

class TestReadonlyMounts(unittest.TestCase):
    
    @patch('builtins.open')
    def test_readonly_root(self, mock_file):
        mock_file.return_value.__enter__ = lambda s: s
        mock_file.return_value.__exit__ = lambda s, *a: None
        mock_file.return_value.__iter__ = lambda s: iter([
            '/dev/sda1 / ext4 ro,relatime 0 0\n'
        ])
        # Mock /proc/version to NOT be WSL
        with patch('builtins.open') as mock_open_all:
            def side_effect(path, *args, **kwargs):
                if path == '/proc/version':
                    m = unittest.mock.mock_open(read_data='Linux version 5.15')()
                    return m
                elif path == '/proc/mounts':
                    m = unittest.mock.mock_open(read_data='/dev/sda1 / ext4 ro,relatime 0 0\n')()
                    m.__iter__ = lambda self: iter(['/dev/sda1 / ext4 ro,relatime 0 0\n'])
                    return m
                return unittest.mock.mock_open()()
            mock_open_all.side_effect = side_effect
            findings = check_readonly_mounts()
            has_critical = any(f['severity'] == 'CRITICAL' for f in findings)
            self.assertTrue(has_critical)

if __name__ == '__main__':
    unittest.main()
