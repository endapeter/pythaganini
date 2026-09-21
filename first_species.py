# first_species.py

"""
First species 1-to-1 counterpoint composition for user-given cantus firmi.

Input contract:
    Series of notes with spaces in between.

    Octave location may be specified using scientific pitch notation:
        C4 D4 E4 F4 G4 A4 B4 C5

    A4 is MIDI note 69, corresponding to 440 Hz.
    C4 is MIDI note 60.

    If no octave is given, DEFAULT_OCTAVE is used.

Output:
    Two aligned strings. If RELATIVE_HEIGHT is "above", the counterpoint is
    printed above the cantus firmus. If RELATIVE_HEIGHT is "below", the
    counterpoint is printed below the cantus firmus.
"""

import re
import scale_info


# --- CONFIGURATION ----------------------------------------------------------

RELATIVE_HEIGHT = "above"       # "above" or "below"
KEY = "auto"                    # "auto" or a key name, e.g. "C", "F", "Bb"
MODE = "auto"                   # "auto", "major", or "minor"
DEFAULT_OCTAVE = 4
MAX_COUNTERPOINT_SPAN = 17      # About an octave + fifth.
ALLOW_MIDDLE_UNISON = False     # If False, unison is only allowed at boundaries.
PRINT_KEY_INFO = False          # If True, prints inferred key/mode before output.

RELATIVE_HEIGHT = str(RELATIVE_HEIGHT).lower()
if RELATIVE_HEIGHT not in {"above", "below"}:
    RELATIVE_HEIGHT = "above"


# --- MUSICAL CONSTANTS ------------------------------------------------------

ALLOWED_VERTICAL_INTERVALS = frozenset({0, 3, 4, 7, 8, 9, 12})
PERFECT_VERTICAL_INTERVALS = frozenset({0, 7, 12})
IMPERFECT_VERTICAL_INTERVALS = frozenset({3, 4, 8, 9})

START_INTERVALS = frozenset({0, 7, 12})
FINAL_INTERVALS = frozenset({0, 12})

CADENCE_INTERVAL_ABOVE = 9      # Major sixth before final octave.
CADENCE_INTERVAL_BELOW = 3      # Minor third before final unison/octave.

LEAP_SEMITONES = 3
LARGE_LEAP_SEMITONES = 5

LETTERS = "CDEFGAB"
LETTER_PC = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

CHROMATIC_SHARP = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

CHROMATIC_FLAT = [
    "C", "Db", "D", "Eb", "E", "F",
    "Gb", "G", "Ab", "A", "Bb", "B"
]

NOTE_RE = re.compile(r"^([A-Ga-g][#b]*)(-?\d+)?$")

# Expected semitone counts for generic melodic intervals.
# Generic interval 1 = unison, 2 = second, ..., 8 = octave.
EXPECTED_MELODIC_SEMITONES = {
    1: {0},
    2: {1, 2},
    3: {3, 4},
    4: {5},
    5: {7},
    6: {8, 9},
    7: {10, 11},
    8: {12},
}

# Expected semitone counts for allowed vertical intervals.
EXPECTED_VERTICAL_SEMITONES = {
    1: {0},        # unison
    3: {3, 4},     # minor/major third
    5: {7},        # perfect fifth
    6: {8, 9},     # minor/major sixth
    8: {12},       # octave
}


# --- BASIC NOTE / MIDI HELPERS ----------------------------------------------

def sign(x):
    return (x > 0) - (x < 0)


def normalize_note_name(name):
    if not name:
        return name
    return name[0].upper() + name[1:]


def accidental_offset(name):
    return name.count("#") - name.count("b")


def base_pitch_value(name):
    """
    Returns the pitch value used for MIDI conversion.

    This is letter pitch + accidental offset, not yet reduced modulo 12.
    Example:
        C4  -> 0
        C#4 -> 1
        Db4 -> -1
        B#4 -> 12
    """
    return LETTER_PC[name[0].upper()] + accidental_offset(name)


def pitch_class_of_name(name):
    return base_pitch_value(name) % 12


def midi_for_name(name, octave):
    """
    Scientific pitch notation MIDI conversion.

    A4 = MIDI 69 = 440 Hz.
    C4 = MIDI 60.
    """
    return 12 * (octave + 1) + base_pitch_value(name)


def octave_for_midi(name, midi):
    """
    Given a spelled note name and a target MIDI number, return the octave
    that makes that spelling equal to that MIDI number.
    """
    return (midi - base_pitch_value(name)) // 12 - 1


def midi_to_frequency(midi):
    """
    Optional helper: converts MIDI note number to frequency.
    A4 = MIDI 69 = 440 Hz.
    """
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def parse_note(token, default_octave=DEFAULT_OCTAVE):
    """
    Parses a note token such as C4, F#3, bb2, D.

    If no octave is supplied, default_octave is used.
    """
    token = token.strip()
    m = NOTE_RE.match(token)
    if not m:
        raise ValueError(f"Cannot parse note: {token!r}")

    name = normalize_note_name(m.group(1))

    if m.group(2) is None:
        octave = default_octave
    else:
        octave = int(m.group(2))

    midi = midi_for_name(name, octave)
    pc = midi % 12
    staff = octave * 7 + LETTERS.index(name[0].upper())

    return {
        "input": token,
        "token": f"{name}{octave}",
        "name": name,
        "octave": octave,
        "midi": midi,
        "pc": pc,
        "staff": staff,
    }


def make_candidate(note_name, midi):
    """
    Builds a counterpoint candidate note from a spelling and target MIDI pitch.
    """
    if pitch_class_of_name(note_name) != midi % 12:
        return None

    octave = octave_for_midi(note_name, midi)
    token = f"{note_name}{octave}"

    return {
        "token": token,
        "name": note_name,
        "octave": octave,
        "midi": midi,
        "pc": midi % 12,
        "staff": octave * 7 + LETTERS.index(note_name[0].upper()),
    }


def sharpen_name(name):
    """
    Raises a note name by one semitone, preserving spelling where practical.
    """
    if not name:
        return name

    letter = name[0].upper()
    acc = name[1:]

    if acc.endswith("b"):
        return letter + acc[:-1]
    if acc == "":
        return letter + "#"
    if acc == "#":
        return letter + "##"
    if acc == "##":
        return name

    return letter + acc + "#"


def chromatic_names(pc):
    names = []
    for name in (CHROMATIC_SHARP[pc], CHROMATIC_FLAT[pc]):
        if name not in names:
            names.append(name)
    return names


# --- SCALE / KEY HELPERS -----------------------------------------------------

def get_scale_names(key, mode):
    """
    Returns scale note names for the given key/mode.

    For minor, the natural minor scale is returned plus the raised leading
    tone, because first-species cadences in minor usually require it.
    """
    if mode == "major":
        return list(scale_info.generate_major_scale(key))

    natural_minor = list(scale_info.generate_minor_scale(key))

    names = []
    for name in natural_minor:
        if name not in names:
            names.append(name)

    if names:
        leading_tone = sharpen_name(names[-1])
        if leading_tone and leading_tone not in names:
            names.append(leading_tone)

    return names


def build_scale_by_pc(names):
    d = {}
    for name in names:
        pc = pitch_class_of_name(name)
        d.setdefault(pc, [])
        if name not in d[pc]:
            d[pc].append(name)
    return d


def scale_pitch_classes(key, mode):
    names = get_scale_names(key, mode)
    return {pitch_class_of_name(name) for name in names}


def choose_key_mode(cf_notes):
    """
    Infers key and mode from the cantus firmus unless overridden by config.
    """
    cf_pcs = {note["pc"] for note in cf_notes}
    last_pc = cf_notes[-1]["pc"]
    first_pc = cf_notes[0]["pc"]

    key_setting = str(KEY)
    mode_setting = str(MODE).lower()

    if mode_setting not in {"major", "minor", "auto"}:
        mode_setting = "auto"

    if key_setting != "auto":
        key_setting = normalize_note_name(key_setting)

    if key_setting != "auto" and mode_setting != "auto":
        return key_setting, mode_setting

    def score_key_mode(key, mode):
        try:
            pcs = scale_pitch_classes(key, mode)
        except Exception:
            return -1
        return len(cf_pcs & pcs)

    candidates = []

    if key_setting != "auto" and mode_setting == "auto":
        candidates = [
            (score_key_mode(key_setting, "major"), key_setting, "major"),
            (score_key_mode(key_setting, "minor"), key_setting, "minor"),
        ]

    elif key_setting == "auto" and mode_setting != "auto":
        if mode_setting == "major":
            keys = scale_info.MAJOR_KEYS.keys()
        else:
            keys = scale_info.MINOR_KEYS.keys()

        candidates = [
            (score_key_mode(k, mode_setting), k, mode_setting)
            for k in keys
        ]

    elif key_setting == "auto" and mode_setting == "auto":
        candidates = [
            (score_key_mode(k, "major"), k, "major")
            for k in scale_info.MAJOR_KEYS.keys()
        ]
        candidates += [
            (score_key_mode(k, "minor"), k, "minor")
            for k in scale_info.MINOR_KEYS.keys()
        ]

    candidates = [c for c in candidates if c[0] >= 0]

    if not candidates:
        return "C", "major"

    def sort_key(item):
        score, key, mode = item
        tonic_pc = pitch_class_of_name(key)

        return (
            score,
            tonic_pc == last_pc,
            tonic_pc == first_pc,
            mode == "major",
            key,
        )

    best = max(candidates, key=sort_key)
    return best[1], best[2]


# --- INTERVAL / MOTION VALIDATION --------------------------------------------

def preferred_cadence_interval():
    if RELATIVE_HEIGHT == "above":
        return CADENCE_INTERVAL_ABOVE
    return CADENCE_INTERVAL_BELOW


def valid_vertical_interval(cf_note, cp_note):
    """
    Checks that the vertical interval is one of the allowed consonances and
    is not spelled as an augmented/diminished interval.
    """
    semitones = abs(cp_note["midi"] - cf_note["midi"])
    if semitones > 12:
        return False

    staff_delta = abs(cp_note["staff"] - cf_note["staff"])
    generic = staff_delta + 1

    if generic > 8:
        return False

    return semitones in EXPECTED_VERTICAL_SEMITONES.get(generic, set())


def valid_melodic_interval(prev_note, curr_note):
    """
    Checks the counterpoint's melodic interval.

    Allows:
        - unison/repetition
        - seconds
        - thirds
        - fourths
        - fifths
        - sixths
        - octaves

    Forbids:
        - augmented/diminished spellings
        - sevenths
        - tritones
        - leaps larger than an octave
    """
    semitones = curr_note["midi"] - prev_note["midi"]
    abs_semitones = abs(semitones)

    if abs_semitones > 12:
        return False

    staff_delta = curr_note["staff"] - prev_note["staff"]
    generic = abs(staff_delta) + 1

    if generic > 8:
        return False

    if abs_semitones not in EXPECTED_MELODIC_SEMITONES.get(generic, set()):
        return False

    # No seventh leaps in strict first species.
    if generic == 7:
        return False

    # Explicit tritone guard.
    if abs_semitones == 6:
        return False

    return True


def motion_type(cf_delta, cp_delta):
    """
    Mathematical motion classification.

    Let:
        cf_delta = cantus firmus MIDI change
        cp_delta = counterpoint MIDI change

    Then:
        cf_delta * cp_delta < 0  => contrary motion
        cf_delta * cp_delta == 0 => oblique or static motion
        cf_delta * cp_delta > 0  => similar motion
    """
    cf_sign = sign(cf_delta)
    cp_sign = sign(cp_delta)

    if cf_sign == 0 and cp_sign == 0:
        return "static"
    if cf_sign == 0 or cp_sign == 0:
        return "oblique"
    if cf_sign == cp_sign:
        return "similar"
    return "contrary"


# --- CANDIDATE GENERATION ----------------------------------------------------

def make_bounds(cf_notes, strict=True):
    """
    Creates MIDI bounds for the generated counterpoint.

    strict=True attempts to keep the counterpoint within MAX_COUNTERPOINT_SPAN.
    strict=False gives the solver more room.
    """
    cf_min = min(note["midi"] for note in cf_notes)
    cf_max = max(note["midi"] for note in cf_notes)
    cf_last = cf_notes[-1]["midi"]

    if RELATIVE_HEIGHT == "above":
        if strict:
            upper = max(cf_max, cf_last + 12)
            lower = max(cf_min, upper - MAX_COUNTERPOINT_SPAN)

            # Do not make the lower bound so high that the lowest CF note
            # cannot receive any consonant note above it.
            lower = min(lower, cf_min + 12)
        else:
            lower = cf_min
            upper = max(cf_max + 12, cf_last + 12)

    else:
        if strict:
            lower = min(cf_min, cf_last - 12)
            upper = min(cf_max, lower + MAX_COUNTERPOINT_SPAN)

            # Do not make the upper bound so low that the highest CF note
            # cannot receive any consonant note below it.
            upper = max(upper, cf_max - 12)
        else:
            lower = min(cf_min - 12, cf_last - 12)
            upper = cf_max

    return lower, upper


def generate_candidates(cf_notes, scale_by_pc, lower, upper):
    """
    For each cantus firmus note, generate possible counterpoint notes.

    Candidates must:
        - be consonant vertically;
        - not cross voices;
        - lie within the given bounds;
        - be spelled as valid intervals.
    """
    all_candidates = []

    # Useful for fallback spelling when the CF contains chromatic notes.
    cf_spellings = {}
    for note in cf_notes:
        cf_spellings.setdefault(note["pc"], [])
        if note["name"] not in cf_spellings[note["pc"]]:
            cf_spellings[note["pc"]].append(note["name"])

    for cf in cf_notes:
        candidates = []
        seen = set()

        def try_add(name, target_midi):
            cand = make_candidate(name, target_midi)
            if cand is None:
                return

            if target_midi < lower or target_midi > upper:
                return

            if RELATIVE_HEIGHT == "above" and cand["midi"] < cf["midi"]:
                return
            if RELATIVE_HEIGHT == "below" and cand["midi"] > cf["midi"]:
                return

            if not valid_vertical_interval(cf, cand):
                return

            key = (cand["midi"], cand["name"])
            if key in seen:
                return

            seen.add(key)
            candidates.append(cand)

        # First pass: diatonic candidates from the inferred key/mode.
        for interval in sorted(ALLOWED_VERTICAL_INTERVALS):
            if RELATIVE_HEIGHT == "above":
                target = cf["midi"] + interval
            else:
                target = cf["midi"] - interval

            pc = target % 12
            names = scale_by_pc.get(pc, [])

            for name in names:
                try_add(name, target)

        # Fallback pass: if no diatonic candidates survived, allow chromatic
        # spellings, preferring spellings already present in the cantus.
        if not candidates:
            for interval in sorted(ALLOWED_VERTICAL_INTERVALS):
                if RELATIVE_HEIGHT == "above":
                    target = cf["midi"] + interval
                else:
                    target = cf["midi"] - interval

                pc = target % 12

                fallback_names = []
                for name in cf_spellings.get(pc, []) + chromatic_names(pc):
                    if name not in fallback_names:
                        fallback_names.append(name)

                for name in fallback_names:
                    try_add(name, target)

        all_candidates.append(candidates)

    return all_candidates


# --- RULE CHECKS --------------------------------------------------------------

def position_hard(i, n, cand, cf, opts):
    """
    Hard vertical rules for a single position.
    """
    interval = abs(cand["midi"] - cf["midi"])

    if interval not in ALLOWED_VERTICAL_INTERVALS:
        return False

    if RELATIVE_HEIGHT == "above" and cand["midi"] < cf["midi"]:
        return False
    if RELATIVE_HEIGHT == "below" and cand["midi"] > cf["midi"]:
        return False

    if not valid_vertical_interval(cf, cand):
        return False

    if (
        interval == 0
        and not opts.get("allow_middle_unison", ALLOW_MIDDLE_UNISON)
        and i not in (0, n - 1)
    ):
        return False

    if opts.get("require_start", False) and i == 0:
        if interval not in START_INTERVALS:
            return False

    if opts.get("require_end", False) and i == n - 1:
        if interval not in FINAL_INTERVALS:
            return False

    # Cadence requirement is only forced for exercises longer than two notes.
    # In a two-note exercise, the first note is simultaneously the beginning
    # and the penultimate cadence note, which can create contradictory demands.
    if opts.get("require_cadence", False) and n > 2 and i == n - 2:
        if interval != preferred_cadence_interval():
            return False

    return True


def transition_hard(prev_cf, prev_cp, curr_cf, curr_cp, i, n, prev_cp_delta):
    """
    Hard rules between adjacent counterpoint/cantus pairs.
    """
    cp_delta = curr_cp["midi"] - prev_cp["midi"]
    cf_delta = curr_cf["midi"] - prev_cf["midi"]

    if not valid_melodic_interval(prev_cp, curr_cp):
        return False

    abs_cp = abs(cp_delta)

    if abs_cp > 12:
        return False

    prev_vert = abs(prev_cp["midi"] - prev_cf["midi"])
    curr_vert = abs(curr_cp["midi"] - curr_cf["midi"])

    if prev_vert not in ALLOWED_VERTICAL_INTERVALS:
        return False
    if curr_vert not in ALLOWED_VERTICAL_INTERVALS:
        return False

    # No consecutive perfect consonances, except in the special two-note case.
    if n > 2:
        if (
            prev_vert in PERFECT_VERTICAL_INTERVALS
            and curr_vert in PERFECT_VERTICAL_INTERVALS
        ):
            return False

    motion = motion_type(cf_delta, cp_delta)

    # No parallel perfect intervals.
    if (
        motion == "similar"
        and prev_vert == curr_vert
        and curr_vert in PERFECT_VERTICAL_INTERVALS
    ):
        return False

    # No direct/hidden perfect intervals approached by a leap.
    if motion == "similar" and curr_vert in PERFECT_VERTICAL_INTERVALS:
        if abs_cp >= LARGE_LEAP_SEMITONES or abs(cf_delta) >= LARGE_LEAP_SEMITONES:
            return False

    # No consecutive large leaps in the same direction in the counterpoint.
    if (
        abs(prev_cp_delta) >= LARGE_LEAP_SEMITONES
        and abs_cp >= LARGE_LEAP_SEMITONES
        and sign(prev_cp_delta) == sign(cp_delta)
        and sign(cp_delta) != 0
    ):
        return False

    return True


# --- SCORING ------------------------------------------------------------------

def candidate_static_score(i, n, cand, cf):
    """
    Score a single vertical sonority.
    """
    interval = abs(cand["midi"] - cf["midi"])
    score = 0.0

    # Prefer imperfect consonances.
    if interval in IMPERFECT_VERTICAL_INTERVALS:
        score += 9.0
    elif interval == 7:
        score += 4.0
    elif interval == 12:
        score += 3.0
    elif interval == 0:
        score += 1.0

    # Beginning preference: unison, octave, fifth.
    if i == 0:
        if interval in START_INTERVALS:
            score += 18.0
        if interval == 12:
            score += 4.0
        elif interval == 0:
            score += 3.0
        elif interval == 7:
            score += 2.0

    # Ending preference: unison or octave.
    if i == n - 1:
        if interval in FINAL_INTERVALS:
            score += 20.0
        if interval == 12:
            score += 4.0
        elif interval == 0:
            score += 3.0

    # Cadence preference: 6-8 above, 3-8/3-1 below.
    if n > 2 and i == n - 2:
        if interval == preferred_cadence_interval():
            score += 35.0

    # Strongly discourage middle unisons even if fallback allows them.
    if interval == 0 and i not in (0, n - 1):
        score -= 30.0

    # Discourage octave spacing in the middle unless necessary.
    if interval == 12 and i not in (0, n - 1):
        score -= 3.0

    return score


def transition_score(prev_cf, prev_cp, curr_cf, curr_cp, i, n, prev_cp_delta):
    """
    Score the motion from one note to the next.

    Contrary motion is derived mathematically:

        cf_delta = CF_midi[i] - CF_midi[i-1]
        cp_delta = CP_midi[i] - CP_midi[i-1]
        dot = cf_delta * cp_delta

        dot < 0  => contrary motion
        dot == 0 => oblique/static motion
        dot > 0  => similar motion
    """
    cp_delta = curr_cp["midi"] - prev_cp["midi"]
    cf_delta = curr_cf["midi"] - prev_cf["midi"]

    abs_cp = abs(cp_delta)
    prev_vert = abs(prev_cp["midi"] - prev_cf["midi"])
    curr_vert = abs(curr_cp["midi"] - curr_cf["midi"])

    score = 0.0

    # Prefer stepwise motion.
    if abs_cp == 0:
        score += 1.0
    elif abs_cp <= 2:
        score += 10.0
    elif abs_cp <= 4:
        score += 5.0
    elif abs_cp <= 7:
        score += 1.0
    elif abs_cp <= 9:
        score -= 2.0
    else:
        score -= 5.0

    # Trajectory / motion-vector scoring.
    dot = cf_delta * cp_delta

    if dot < 0:
        # Contrary motion: stronger negative dot product gets higher score.
        score += 8.0 + min(12.0, float(-dot))
    elif dot == 0:
        # Oblique motion.
        score += 4.0
    else:
        # Similar motion.
        score -= min(8.0, float(dot))

    motion = motion_type(cf_delta, cp_delta)

    if motion == "contrary":
        score += 6.0
    elif motion == "oblique":
        score += 3.0
    elif motion == "similar":
        score -= 2.0

    # Vertical quality at the new note.
    if curr_vert in IMPERFECT_VERTICAL_INTERVALS:
        score += 8.0
    elif curr_vert in PERFECT_VERTICAL_INTERVALS:
        if i == n - 1:
            score += 8.0
        elif i == 0:
            score += 3.0
        else:
            score -= 4.0

    # Cadence scoring.
    if n > 1 and i == n - 1:
        if curr_vert in FINAL_INTERVALS:
            score += 18.0

        if prev_vert == preferred_cadence_interval():
            score += 35.0

        # A cadence approached by contrary motion is especially good.
        if dot < 0:
            score += 10.0

    if n > 2 and i == n - 2:
        if curr_vert == preferred_cadence_interval():
            score += 25.0

    # After a large leap, prefer opposite-direction recovery.
    if abs(prev_cp_delta) >= LARGE_LEAP_SEMITONES:
        if sign(cp_delta) == -sign(prev_cp_delta) and abs_cp <= 4:
            score += 10.0
        elif sign(cp_delta) == sign(prev_cp_delta):
            score -= 8.0

    # Discourage consecutive leaps in the same direction.
    if (
        abs(prev_cp_delta) >= LEAP_SEMITONES
        and abs_cp >= LEAP_SEMITONES
        and sign(prev_cp_delta) == sign(cp_delta)
        and sign(cp_delta) != 0
    ):
        score -= 7.0

    # Discourage direct/hidden perfect consonances even when stepwise.
    if motion == "similar" and curr_vert in PERFECT_VERTICAL_INTERVALS:
        score -= 10.0

    return score


# --- SEARCH / SOLVER ----------------------------------------------------------

def solve_counterpoint(cf_notes, candidates, opts):
    """
    Dynamic-programming search for the highest-scoring valid counterpoint line.
    """
    n = len(cf_notes)

    if n == 0:
        return []

    dp = [dict() for _ in range(n)]
    back = [dict() for _ in range(n)]

    # Initial states.
    for idx, cand in enumerate(candidates[0]):
        if not position_hard(0, n, cand, cf_notes[0], opts):
            continue

        key = (idx, 0)
        dp[0][key] = candidate_static_score(0, n, cand, cf_notes[0])

    if not dp[0]:
        return None

    # Build states note by note.
    for i in range(1, n):
        for prev_key, prev_score in dp[i - 1].items():
            prev_idx, prev_cp_delta = prev_key
            prev_cand = candidates[i - 1][prev_idx]
            prev_cf = cf_notes[i - 1]

            for curr_idx, curr_cand in enumerate(candidates[i]):
                if not position_hard(i, n, curr_cand, cf_notes[i], opts):
                    continue

                if not transition_hard(
                    prev_cf,
                    prev_cand,
                    cf_notes[i],
                    curr_cand,
                    i,
                    n,
                    prev_cp_delta,
                ):
                    continue

                cp_delta = curr_cand["midi"] - prev_cand["midi"]

                score = prev_score + transition_score(
                    prev_cf,
                    prev_cand,
                    cf_notes[i],
                    curr_cand,
                    i,
                    n,
                    prev_cp_delta,
                )

                new_key = (curr_idx, cp_delta)

                if new_key not in dp[i] or score > dp[i][new_key]:
                    dp[i][new_key] = score
                    back[i][new_key] = prev_key

        if not dp[i]:
            return None

    # Choose best final state.
    best_key = max(dp[n - 1], key=lambda k: dp[n - 1][k])

    # Reconstruct path.
    result = [None] * n
    key = best_key

    for i in range(n - 1, 0, -1):
        result[i] = candidates[i][key[0]]
        key = back[i][key]

    result[0] = candidates[0][key[0]]

    return result


def generate_counterpoint(cf_notes):
    """
    Generates a counterpoint line for the given cantus firmus.

    Returns:
        (counterpoint_notes, key, mode)

    If no solution is found, returns:
        (None, key, mode)
    """
    if not cf_notes:
        return [], "C", "major"

    key, mode = choose_key_mode(cf_notes)

    try:
        scale_names = get_scale_names(key, mode)
    except Exception:
        key, mode = "C", "major"
        scale_names = get_scale_names(key, mode)

    scale_by_pc = build_scale_by_pc(scale_names)

    base_option_sets = [
        {
            "require_start": True,
            "require_end": True,
            "require_cadence": True,
        },
        {
            "require_start": True,
            "require_end": True,
            "require_cadence": False,
        },
        {
            "require_start": True,
            "require_end": False,
            "require_cadence": False,
        },
        {
            "require_start": False,
            "require_end": True,
            "require_cadence": False,
        },
        {
            "require_start": False,
            "require_end": False,
            "require_cadence": False,
        },
    ]

    # Try strict range first, then a wider range if necessary.
    for strict_bounds in (True, False):
        lower, upper = make_bounds(cf_notes, strict=strict_bounds)
        candidates = generate_candidates(cf_notes, scale_by_pc, lower, upper)

        if any(not c for c in candidates):
            continue

        # Try strict unison rules first, then allow middle unisons if needed.
        for allow_middle_unison in (False, True):
            for base_opts in base_option_sets:
                opts = dict(base_opts)
                opts["allow_middle_unison"] = allow_middle_unison

                result = solve_counterpoint(cf_notes, candidates, opts)
                if result is not None:
                    return result, key, mode

    return None, key, mode


# --- OUTPUT -------------------------------------------------------------------

def format_output(cf_notes, cp_notes):
    """
    Returns two aligned lines according to RELATIVE_HEIGHT.
    """
    cf_tokens = [note["token"] for note in cf_notes]
    cp_tokens = [note["token"] for note in cp_notes]

    widths = [
        max(len(cf_token), len(cp_token))
        for cf_token, cp_token in zip(cf_tokens, cp_tokens)
    ]

    cf_line = " ".join(
        token.ljust(width)
        for token, width in zip(cf_tokens, widths)
    ).rstrip()

    cp_line = " ".join(
        token.ljust(width)
        for token, width in zip(cp_tokens, widths)
    ).rstrip()

    if RELATIVE_HEIGHT == "above":
        return cp_line, cf_line

    return cf_line, cp_line


def main():
    try:
        raw = input("Input cantus firmus: ").strip()
    except EOFError:
        return

    tokens = raw.replace(",", " ").split()

    try:
        cf_notes = [parse_note(token) for token in tokens if token]
    except ValueError as e:
        print(f"Invalid input: {e}")
        return

    if not cf_notes:
        print("No notes entered.")
        return

    counterpoint, key, mode = generate_counterpoint(cf_notes)

    if counterpoint is None:
        print("No counterpoint could be generated under the current rules/configuration.")
        return

    if PRINT_KEY_INFO:
        print(f"Key: {key} {mode}")

    top_line, bottom_line = format_output(cf_notes, counterpoint)

    print(top_line)
    print(bottom_line)


if __name__ == "__main__":
    main()