"""Conventions: what a convention is, and how one is established from evidence.

A convention is a four-tuple (situation, dispreferred form, preferred form, evidence). Its life
stage is a vector -- applied / followed / enforced / stated / discussed -- and each component has
its own source. Measured before this package existed: the sources disagree, and the disagreement
is the stage. `grind` is applied in 534 commits and enforced in 21 comments; dot notation is
enforced in 224 comments and followed by 14% of applicable declarations. No single substrate
suffices, which is why this is a package and not a census.
"""
