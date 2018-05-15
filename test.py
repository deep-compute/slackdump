import doctest
import unittest

from slackdump import slackdump

def suitefn():
    suite = unittest.TestSuite()
    suite.addTests(doctest.DocTestSuite(slackdump))
    return suite


if __name__ == "__main__":
    doctest.testmod(slackdump)
