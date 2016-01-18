# __init__.py
r'''
instructions on module use.
should deal with
    1. record type assessment
    2. record feed import
    3. field parsing
    4. recon obj prelim creation with fields, query
    5. recon obj expansion with calls
    6. present results back
    7. update records
'''

from .entities import *
from .exceptions import *
from .constants import *

if __name__ == "__main__":
    import doctest
    doctest.testmod()
