import unittest
from bookied import utils


class Testcases(unittest.TestCase):
    def test_resolve_hostnames(self):
        self.assertEqual(["127.0.0.1"], utils.resolve_hostnames(["localhost"]))

    def test_dlist2dict(self):
        self.assertEqual(utils.dList2Dict([["a", "b"]]), dict(a="b"))

    def test_dict2dlist(self):
        self.assertEqual(utils.dict2dList(dict(a="b")), [["a", "b"]])
