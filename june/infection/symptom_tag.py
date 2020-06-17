from enum import IntEnum


class SymptomTag(IntEnum):
    """
    A tag for the symptoms exhibited by a person.

    Higher numbers are more severe.
    0 - 5 correspond to indices in the health index array.
    """

    recovered = -3
    healthy = -2
    exposed = -1
    asymptomatic = 0
    influenza = 1
    pneumonia = 2
    hospitalised = 3
    intensive_care = 4
    dead = 5

    @classmethod
    def from_string(cls, string: str) -> "SymptomTag":
        for item in SymptomTag:
            if item.name == string:
                return item
        raise AssertionError(
            f"{string} is not the name of a SymptomTag"
        )