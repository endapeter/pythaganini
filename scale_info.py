# scale_info.py

PITCHES = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0
}


MAJOR_KEYS = {
    "C":  [],
    "G":  ["F#"],
    "D":  ["F#", "C#"],
    "A":  ["F#", "C#", "G#"],
    "E":  ["F#", "C#", "G#", "D#"],
    "B":  ["F#", "C#", "G#", "D#", "A#"],
    "F#": ["F#", "C#", "G#", "D#", "A#", "E#"],
    "C#": ["F#", "C#", "G#", "D#", "A#", "E#", "B#"],

    "F":  ["Bb"],
    "Bb": ["Bb", "Eb"],
    "Eb": ["Bb", "Eb", "Ab"],
    "Ab": ["Bb", "Eb", "Ab", "Db"],
    "Db": ["Bb", "Eb", "Ab", "Db", "Gb"],
    "Gb": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
    "Cb": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Fb"],
}

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]


def generate_major_scale(key):
    """Generate a correctly-spelled major scale."""
    scale = []

    tonic_pitch = PITCHES[key]

    # Letter names must progress alphabetically.
    letters = ["C", "D", "E", "F", "G", "A", "B"]
    tonic_letter = key[0]
    start = letters.index(tonic_letter)

    for i, semitones in enumerate(MAJOR_SCALE):
        pitch = (tonic_pitch + semitones) % 12
        letter = letters[(start + i) % 7]

        # Find the spelling that matches the required letter.
        for note, note_pitch in PITCHES.items():
            if note_pitch == pitch and note[0] == letter:
                scale.append(note)
                break

    return scale


MINOR_KEYS = {
    "A": "A",
    "E": "E",
    "B": "B",
    "F#": "F#",
    "C#": "C#",
    "G#": "G#",
    "D#": "D#",
    "A#": "A#",

    "D": "D",
    "G": "G",
    "C": "C",
    "F": "F",
    "Bb": "Bb",
    "Eb": "Eb",
    "Ab": "Ab",
    "Db": "Db",
}


def generate_minor_scale(key):
    """Generate a natural minor scale with correct spelling."""
    major_relative = {
        "A": "C", "E": "G", "B": "D", "F#": "A",
        "C#": "E", "G#": "B", "D#": "F#", "A#": "C#",
        "D": "F", "G": "Bb", "C": "Eb", "F": "Ab",
        "Bb": "Db", "Eb": "Gb", "Ab": "Cb", "Db": "Fb"
    }

    # Natural minor = major scale starting on the relative major's 6th degree
    relative_major = major_relative[key]
    major = generate_major_scale(relative_major)

    return major[5:] + major[:5]


def scale_degree(key, degree, mode="major"):
    if mode == "major":
        scale = generate_major_scale(key)
    elif mode == "minor":
        scale = generate_minor_scale(key)
    else:
        raise ValueError("mode must be 'major' or 'minor'")

    if not 1 <= degree <= 7:
        raise ValueError("degree must be between 1 and 7")

    return scale[degree - 1]