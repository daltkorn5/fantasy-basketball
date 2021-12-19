"""Helpful functions that can be used across classes"""
from unidecode import unidecode
import re


def sanitize_player_name(player_name: str) -> str:
    """Helper function to sanitize player names.

    This is meant to make it easier to join data from multiple sources
    by standardizing the player names. It consists of replacing any
    non-ascii characters, stripping out any suffixes (like Jr or III),
    and removing any periods in a player's name (like C.J. McCollum vs CJ McCollum)

    :param player_name: The name that you want to sanitize
    :return: The player name modified as described above
    """
    ascii_characters = unidecode(player_name)
    without_dots = ascii_characters.replace(".", "")
    without_suffixes = re.sub(r"( Jr| IV| III| II| Sr)", "", without_dots)
    return without_suffixes
