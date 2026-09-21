<p align="center">
  <img width="200" src="logo.png"> 
</p>

<h1> <p align="center">
      pythaganini
</p> </h1>

Currently, only the first species counterpoint function is implemented.

`first_species.py` is a rule-based first species (1:1) counterpoint generator for a user-supplied cantus firmus.

It takes a single line of note names, optionally with octave numbers, and generates a second voice above or below the cantus firmus according to strict first species counterpoint conventions.

The script depends on `scale_info.py`.

---

## Features

- **First species 1:1 counterpoint generation**
  - One counterpoint note against each cantus firmus note.
  - Works for counterpoint **above** or **below** the cantus firmus.

- **Scientific pitch notation support**
  - Notes may include octave numbers.
  - `A4` is treated as MIDI note `69`, corresponding to `440 Hz`.
  - `C4` is MIDI note `60`.

- **Automatic key and mode inference**
  - The script can infer a likely major or minor key from the input.
  - Key and mode can also be set manually.

- **Rule-based voice leading**
  - Consonances only.
  - Prefers imperfect consonances.
  - Avoids parallel perfect intervals.
  - Avoids hidden/direct perfect intervals approached by leap.
  - Encourages contrary motion.
  - Discourages excessive leaps.
  - Requires or prefers stylistically appropriate beginning and ending intervals.

- **Aligned text output**
  - The generated counterpoint is printed above or below the original cantus firmus.
  - Notes are column-aligned for readability.

---

## Requirements

- Python 3.8 or later
- `scale_info.py` in the same directory

No external packages are required.

---

## Usage

Run the script:

```bash
python first_species.py
```

You will be prompted to enter a cantus firmus:

```text
Input cantus firmus:
```

Enter notes separated by spaces.

## Configuration

Configuration options are located near the top of `first_species.py`.

### `RELATIVE_HEIGHT`

Determines whether the generated counterpoint is above or below the cantus firmus.

```python
RELATIVE_HEIGHT = "above"
```

Options:

```python
RELATIVE_HEIGHT = "above"
RELATIVE_HEIGHT = "below"
```

---

### `KEY`

Sets the key used for counterpoint generation.

```python
KEY = "auto"
```

Options:

```python
KEY = "auto"
KEY = "C"
KEY = "G"
KEY = "F"
KEY = "Bb"
KEY = "Eb"
KEY = "A"
KEY = "D"
# etc.
```

If `KEY = "auto"`, the script attempts to infer the key from the input notes.

---

### `MODE`

Sets the mode used for counterpoint generation.

```python
MODE = "auto"
```

Options:

```python
MODE = "auto"
MODE = "major"
MODE = "minor"
```

If `MODE = "auto"`, the script attempts to infer whether the cantus firmus is major or minor.

---

### `DEFAULT_OCTAVE`

Used when a note has no octave number.

```python
DEFAULT_OCTAVE = 4
```

---

### `MAX_COUNTERPOINT_SPAN`

The preferred maximum range of the generated counterpoint line, measured in semitones.

```python
MAX_COUNTERPOINT_SPAN = 17
```

`17` semitones is approximately an octave plus a fifth.

The script tries to keep the counterpoint within this range, but may exceed it if necessary to find a valid solution.

---

### `ALLOW_MIDDLE_UNISON`

Controls whether unisons are allowed in the middle of the phrase.

```python
ALLOW_MIDDLE_UNISON = False
```

Strict style usually avoids unisons except at the beginning or end.

---

### `PRINT_KEY_INFO`

If enabled, prints the inferred or configured key and mode.

```python
PRINT_KEY_INFO = False
```

Example when enabled:

```text
Key: C major
```

---

## Counterpoint Rules Implemented

### 1. Vertical intervals

Only consonant intervals are allowed:

- Unison
- Minor third
- Major third
- Perfect fifth
- Minor sixth
- Major sixth
- Octave

In semitones:

```text
0, 3, 4, 7, 8, 9, 12
```

Imperfect consonances are preferred:

```text
3, 4, 8, 9
```

Unisons are generally only allowed at the beginning or end.

---

### 2. Beginning

The generator prefers the first interval to be one of:

- Unison
- Perfect fifth
- Octave

In semitones:

```text
0, 7, 12
```

The script first tries to enforce this rule. If no solution can be found, it may relax the requirement.

---

### 3. Ending

The generator prefers the final interval to be one of:

- Unison
- Octave

In semitones:

```text
0, 12
```

The script first tries to enforce this rule. If no solution can be found, it may relax the requirement.

---

### 4. Cadence preference

For a phrase long enough to have a cadence, the generator prefers:

#### Counterpoint above the cantus firmus

```text
Major sixth -> Octave
```

Example:

```text
Counterpoint: A4 -> C5
Cantus:       C4 -> C4
```

#### Counterpoint below the cantus firmus

```text
Minor third -> Unison or Octave
```

This is implemented as a strong preference, not an absolute requirement, because arbitrary user-supplied cantus firmi may not always support the ideal cadence.

---

### 5. Melodic motion

The generated counterpoint line prefers stepwise motion.

Allowed melodic intervals include:

- Second
- Third
- Fourth
- Fifth
- Sixth
- Octave

The generator avoids:

- Sevenths
- Tritones
- Augmented intervals
- Diminished intervals
- Leaps larger than an octave

Large leaps are discouraged, especially when repeated in the same direction.

---

### 6. Leap handling

The script applies the following melodic leap rules:

- Large leaps are discouraged.
- Consecutive large leaps in the same direction are forbidden.
- After a large leap, motion in the opposite direction is strongly preferred.
- Repeated leap motion in the same direction is penalized.

---

### 7. Parallel and hidden intervals

The generator avoids:

- Parallel unisons
- Parallel fifths
- Parallel octaves
- Consecutive perfect consonances where possible
- Direct/hidden fifths and octaves approached by leap

Similar motion into a perfect interval is treated cautiously, especially if one voice leaps.

---

### 8. Voice crossing

Voice crossing is forbidden.

If `RELATIVE_HEIGHT = "above"`, the counterpoint will not go below the cantus firmus.

If `RELATIVE_HEIGHT = "below"`, the counterpoint will not go above the cantus firmus.

---

### 9. Range

The script attempts to keep the generated counterpoint within a reasonable vocal range.

The preferred span is controlled by:

```python
MAX_COUNTERPOINT_SPAN = 17
```

This is approximately an octave plus a fifth.

If strict range constraints make the input impossible to set, the script may widen the allowed range.

---

## Key and Mode Inference

When `KEY = "auto"` and/or `MODE = "auto"`, the script compares the pitch classes of the cantus firmus against known major and minor scales.

It prefers keys that:

1. Contain the most notes from the cantus firmus.
2. Have a tonic matching the final note.
3. Have a tonic matching the first note.
4. Prefer major over minor in ties.

If no suitable key is found, the script defaults to:

```text
C major
```

---

## Limitations

This script is a pedagogical rule-based composer, not a full Renaissance-style counterpoint engine.

Current limitations include:

- It primarily uses diatonic notes from the inferred key.
- Chromatic cantus firmi may produce limited results.
- Minor mode handling is simplified.
- Cadence rules are strongly preferred but not always possible.
- The output is stylistically guided by rules and scoring, but not guaranteed to be musically inspired.

---

## Extending the Script

Second species counterpoint script is work-in-progress.
