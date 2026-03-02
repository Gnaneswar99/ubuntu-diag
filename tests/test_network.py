"""Test network diagnostics"""

import unittest
from unittest.mock import patch
import socket
from diag.network import check_dns_resolution, check_default_route

class TestDNS(unittest.TestCase):
    
    @patch('socket.getaddrinfo')
    def test_dns_working(self, mock_dns):
        mock_dns.return_value = [(2, 1, 6, '', ('185.125.190.20', 0))]
        findings = check_dns_resolution()
        self.assertEqual(findings[0]['severity'], 'OK')
    
    @patch('socket.getaddrinfo', side_effect=socket.gaierror('DNS failed'))
    def test_dns_failure(self, mock_dns):
        findings = check_dns_resolution()
        self.assertEqual(findings[0]['severity'], 'CRITICAL')

class TestDefaultRoute(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_route_exists(self, mock_run):
        mock_run.return_value.stdout = 'default via 192.168.1.1 dev eth0\n'
        mock_run.return_value.returncode = 0
        findings = check_default_route()
        self.assertEqual(findings[0]['severity'], 'OK')
    
    @patch('subprocess.run')
    def test_no_route(self, mock_run):
        mock_run.return_value.stdout = ''
        mock_run.return_value.returncode = 0
        findings = check_default_route()
        self.assertEqual(findings[0]['severity'], 'CRITICAL')

if __name__ == '__main__':
    unittest.main()
