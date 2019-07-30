import doctest
import unittest

from slackdump import slackdump
from slackdump import slackhistory


def suitefn():
    suite = unittest.TestSuite()
    suite.addTests(doctest.DocTestSuite(slackdump))
    suite.addTests(doctest.DocTestSuite(slackhistory))
    return suite


if __name__ == "__main__":
    doctest.testmod(slackdump)
    doctest.testmod(slackhistory)
