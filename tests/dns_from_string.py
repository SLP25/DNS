import unittest
import sys
import os
sys.path.append(os.path.abspath('../common'))
from dnsEntry import DNSEntry, EntryType
from exceptions import InvalidDNSEntry

class TestDNSFromString(unittest.TestCase):

    def test_one(self):
        dns1 = DNSEntry("ns1 A 193.136.130.250 200", fromFile = True)
        self.assertEqual(dns1.parameter, "ns1")
        self.assertEqual(dns1.type, EntryType.A)
        self.assertEqual(dns1.value, "193.136.130.250")
        self.assertEqual(dns1.ttl, 200)
        self.assertEqual(dns1.priority, 0)

    def test_two(self):
        dns1 = DNSEntry("ns1 A 193.136.130.250 200 69", fromFile = True)
        self.assertEqual(dns1.parameter, "ns1")
        self.assertEqual(dns1.type, EntryType.A)
        self.assertEqual(dns1.value, "193.136.130.250")
        self.assertEqual(dns1.ttl, 200)
        self.assertEqual(dns1.priority, 69)

    def test_three(self):
        dns1 = DNSEntry("batata CNAME lttstore.com 255 69", fromFile = True)
        self.assertEqual(dns1.parameter, "batata")
        self.assertEqual(dns1.type, EntryType.CNAME)
        self.assertEqual(dns1.value, "lttstore.com")
        self.assertEqual(dns1.ttl, 255)
        self.assertEqual(dns1.priority, 69)

    def test_four(self):
        with self.assertRaises(InvalidDNSEntry):
            DNSEntry("batata NONE lttstore.com 255 69", fromFile = True)


if __name__ == '__main__':
    unittest.main()