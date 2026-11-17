#!/usr/bin/env python3
"""
A Reel script says its numbers out loud: "five hours", "twenty minutes",
"two thousand dollars". `/ig-reel` sends every script through `/ig-human`, so
`detect.py` has to count those as concrete, or every spoken script loses its
SPECIFICITY score for being written the way it will be said.

This checks four things:

  1. The same script written with number words and with digits gets about the
     same SPECIFICITY score.
  2. A number said in several words ("twenty-five thousand") counts once, the
     way "25,000" matches once. Otherwise spelled-out scripts would score
     higher than the same script in digits.
  3. A hook with a hyphenated number ("Twenty-five things...") scores the same
     in hookscore.py as the hook with the digits, and beats.py counts it once.
     Both keep hyphens inside a word, so "twenty-five" is one word to them.
  4. detect.py, hookscore.py and beats.py use the same word lists. Each skill
     folder has to work when it is installed on its own, so the lists are
     copied, and this is what stops the copies drifting apart.

    python3 tests/test_spoken_numbers.py

Also runs under pytest. Exits non-zero if any check fails.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")


def load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SKILLS, *parts))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detect = load("ig_human_detect", "ig-human", "detect.py")
hookscore = load("ig_reel_hookscore", "ig-reel", "hookscore.py")
beats = load("ig_reel_beats", "ig-reel", "beats.py")

SPELLED = """\
I used to spend five hours a week on captions.
Now it takes me twenty minutes.
Here's what changed.
Before I film, I write down four things.
The hook, the point, the proof and the ask.
That cut my editing time in half and saved me two thousand dollars a year.
Comment CLAUDE and I'll send you the list.
"""

DIGITS = """\
I used to spend 5 hours a week on captions.
Now it takes me 20 minutes.
Here's what changed.
Before I film, I write down 4 things.
The hook, the point, the proof and the ask.
That cut my editing time by 50% and saved me 2,000 dollars a year.
Comment CLAUDE and I'll send you the list.
"""

TAIL = (" in the first month, and most of it came from people who had watched"
        " every single reel we posted that whole year before the launch.")


def markers(text):
    """The count at the front of check_specificity's detail line."""
    score, detail = detect.check_specificity(text)
    assert detail[0].isdigit(), "too short to judge: %r" % text
    return int(detail.split()[0])


def test_spelled_and_digit_scripts_score_alike():
    spelled, _ = detect.check_specificity(SPELLED)
    digits, _ = detect.check_specificity(DIGITS)
    assert spelled >= 50, "spelled-out script scored %.1f on SPECIFICITY" % spelled
    assert abs(spelled - digits) <= 10, (
        "spelled %.1f vs digits %.1f on SPECIFICITY" % (spelled, digits))
    # Both scores can sit at the 100 cap, so compare what was counted too.
    assert markers(SPELLED) == markers(DIGITS), (
        "spelled %d markers vs digits %d" % (markers(SPELLED), markers(DIGITS)))


def test_number_said_in_several_words_counts_once():
    spelled = markers("We raised twenty-five thousand" + TAIL)
    digits = markers("We raised 25,000" + TAIL)
    assert spelled == digits == 1, "twenty-five thousand: %d, 25,000: %d" % (spelled, digits)


# The same hook with the number spelled out and in digits. The second one has
# nothing else in it that FRONTLOAD counts, so it also checks that the number
# is found as the payload, not just counted.
HYPHENATED = [
    ("Twenty-five things I wish I knew", "25 things I wish I knew"),
    ("Thirty-five reels later, here is what my editing looks like",
     "35 reels later, here is what my editing looks like"),
]


def test_hyphenated_number_hook_scores_like_digits():
    for spelled, digits in HYPHENATED:
        # "twenty-five" is one spoken word group, so LENGTH still sees one word.
        assert len(hookscore.words(spelled)) == len(hookscore.words(digits)), (
            "%r has %d words, %r has %d" % (spelled, len(hookscore.words(spelled)),
                                            digits, len(hookscore.words(digits))))
        ours, overall, _, _ = hookscore.run(spelled)
        theirs, overall_digits, _, _ = hookscore.run(digits)
        for check in hookscore.CHECKS:
            assert ours[check][0] == theirs[check][0], "%s: %r %.1f (%s) vs %r %.1f (%s)" % (
                check, spelled, ours[check][0], ours[check][1],
                digits, theirs[check][0], theirs[check][1])
        assert overall == overall_digits, "%r %.1f vs %r %.1f" % (
            spelled, overall, digits, overall_digits)
        # Counted once, not once per half.
        count = int(ours["SPECIFICITY"][1].split()[0])
        assert count == 1, "%r: %d concrete markers" % (spelled, count)


def test_beats_counts_hyphenated_number_once():
    for spelled, digits in HYPHENATED:
        assert beats.concrete(spelled) == beats.concrete(digits) == 1, (
            "%r: %d, %r: %d" % (spelled, beats.concrete(spelled),
                                digits, beats.concrete(digits)))


def test_word_lists_match_hookscore_and_beats():
    for name in ("SPOKEN_NUMBERS", "MONEY_WORDS"):
        ours = getattr(detect, name)
        for other in (hookscore, beats):
            theirs = getattr(other, name)
            assert ours == theirs, "%s differs from %s: %s" % (
                name, os.path.basename(other.__file__), sorted(ours ^ theirs))


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("  ok    %s" % name)
        except Exception as err:          # AssertionError, or a missing list
            failed += 1
            print("  FAIL  %s\n        %s: %s" % (name, type(err).__name__, err))
    print()
    print("%d of %d checks pass" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
