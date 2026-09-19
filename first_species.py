# first_species.py

"""
First species 1-to-1 counterpoint composition for user-given cantus firmi.

Input contract: series of notes with spaces in between, e.g. "C F E A G F E D C".

Outputs two strings, original cantus firmus is returned with generated counterpoint above or below (set by variables) in a correspondance above or below the original string.
"""

import scale_info

# --- CONFIGURATION ---
RELATIVE_HEIGHT = "above"

# --- GET INFO ---
cantus_firmus = input("Input cantus firmus: ").split() # do input sanitation later
melody_length = len(cantus_firmus)


print(scale_info.generate_major_scale("F"))
print(scale_info.scale_degree("D", 3))