"""
All the exceptions used in this program. 
"""
class LoginException(Exception):
    """Credentials were not accepted in some step."""
class StateException(Exception):
    """An invalid state was detected."""
class EarlyLeaveException(Exception):
    """Leave the run process early. Controlled panic, basically."""
