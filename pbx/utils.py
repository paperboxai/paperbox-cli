"""
This module provides general utility functions used within PBX-CLI.
"""


import re


def string_to_identifier(name: str) -> str:
    """Generate a human readable yet database-friendly id from an object's name
     by removing all non-alphanumerical characters and uppercasing

    Args:
        name (str): name

    Returns:
        str: id
    """
    return re.sub("[^A-Za-z0-9_.]+", "", name).upper().replace(".", "_")
