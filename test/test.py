from test_batoto import *
from test_dynastyscans import *
from test_madokami import *
import sys
import unittest

if __name__ == '__main__':
    devnull = open(os.devnull, 'w')
    sys.stdout = devnull
    unittest.main()
    devnull.close()
