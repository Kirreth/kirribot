# utils/database/leveling.py
import math

def berechne_level(counter: int) -> int:
    """
    Berechnet das Level anhand der Gesamtzahl der Nachrichten.
    z.B. Level = floor(sqrt(counter))
    """
    return max(1, int(math.sqrt(counter)))

def berechne_level_und_rest(counter: int):
    """
    Berechnet Level und Nachrichten, die bis zum nächsten Level fehlen.
    """
    level = berechne_level(counter)
    # Nächstes Level = (level + 1)^2
    next_level_threshold = (level + 1) ** 2
    rest = max(0, next_level_threshold - counter)
    return level, rest
