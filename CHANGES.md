# What we changed in instagram-agent-skill

This fork, by Artur Rioni, starts from [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill) at commit `d03c56b` (13 Sep 2026, that repo's last commit), MIT. The first round of changes is the one commit on top of his (`git diff d03c56b d902f52`): 22 files changed, plus one new test and this file. Fixes made after that are under "Later fixes" at the end.

Before anything ran, all six Python scripts were read in full: standard library only, no network, no shell calls, they only read the files you hand them and write where you tell them. They were run with `python3 -I` from outside the folder.

## Pull requests taken from Jake's repo

Each diff was read as untrusted code and checked by running the tools afterwards.

| PR | Author | What it fixes | Taken? |
| --- | --- | --- | --- |
| #18 | barberstats | Weak openers matched as prefixes, so every hook starting "you" or "your" lost 30 points (issue #17) | Yes |
| #52 | cbordoni1 | Six hook formulas couldn't recognise their own example; adds a test for all 26 | Yes. 26 of 26 examples now classify as their own formula (it was 20) |
| #66 | thecloudseo | The same six formulas | No: #52 does the same job more carefully. #66 lets "one" open a listicle, which the scorer treats as filler, and lets a quote open with one mark and close with another |
| #5 | ganeshphutane-g | Capitalised sentence starts counted as names; beats now count spoken numbers ("five hours"); `swipe.py --out` crashed on a bare file name; hashtag wall rule and caption description moved to five tags; corrected example scores | Yes. The example scores it wrote match the patched scorer exactly |
| #33 | iliyami | The humanizer split joined emoji (👨‍👩‍👧, 🏳️‍🌈) and broke Persian, Arabic and Indic words (issue #29, bug 1) | Yes |
| #58 | dougtudino | Emoji crash on Windows pipes; dollar amounts in SKILL.md | The UTF-8 part, yes. The dollar part we solved by rewording instead (below) |
| #67 | beyondtheaddress | "Fix audited bugs": 6,657 added lines across 93 files | No. It's a rewrite, not a fix: new scripts (one runs Node through `subprocess`), a CI workflow and a test corpus. Too big to vet and it changes what the plugin is |

## Issues fixed by us

- **#17** (hooks starting "you" lose 30 points): fixed by #18. Checked: "Your captions get cut…" now scores FRONTLOAD 100.
- **#29**, seven bugs:
  1. Joined emoji split: fixed by #33. Checked: all three joiners kept, FINGERPRINT 100.
  2. "In this video I'm going to show you" and "stop scrolling" were deleted before the scan that's meant to flag them. Removed those four entries from the lexicon's phrases, so the structure checks flag them instead of the cleaner deleting them.
  3. "Save this for later" was deleted, though `/ig-caption` and `/ig-reel` recommend it as the one ask. Removed from the lexicon.
  4. A name could never count as a hook's payload (the name pattern can't match a single word). Names are now found in the whole line first. Checked: "The day Netflix called me back" now finds its payload.
  5. A lexicon term ending in punctuation ("what are your thoughts?") could never match. Word boundaries now only go on edges that are letters, in both `humanize.py` and `detect.py`.
  6. "Comment below" counted as a keyword ask. Only the verb is case-insensitive now: "Comment CLAUDE" counts, "Comment below" doesn't.
  7. "Nobody is talking about this" became "few people do this", which changes the claim. Now "few people talk about this" (and the same for "no one is talking about this").
- **#46**, three parts:
  1. Script commands only worked from inside the skill folder. Every command now uses the skill's full path (`<skill dir>`, the "Base directory for this skill" Claude is shown, or `${CLAUDE_PLUGIN_ROOT}/skills/…` in the plugin). The README's examples now run from the repo root.
  2. The carousel step made a PDF; Instagram needs one image per slide. It now screenshots each slide to PNG (headless Chrome or any HTML-to-image tool), with a fallback to hand the copy over for Canva.
  3. Edits to `slop.json` were lost on every plugin update. Both scripts now use `~/.claude/instagram/slop.json` when it exists, and `/ig-human` says so.

## Other fixes we made

- Multi-word lexicon terms only matched single spaces, because since Python 3.7 `re.escape` doesn't escape spaces, so the code's `\ ` replacement never ran. Any run of spaces matches now.
- Dollar amounts in two SKILL.md examples ("$18,000", "$4,200") start with `$1`/`$4`, which Claude Code can read as a command argument. #58 put a backslash in front, which only helps if Claude Code honours it, so we reworded them instead ("18K", "4,200 dollars").
- The README's manual install failed on a fresh machine with no `~/.claude/skills` folder (issue #59). Added `mkdir -p`.
- The lexicon count in the docs went from 154 to 149 terms (five entries removed above).

## Platform facts brought up to date

Sources: the Instagram Help Center pages and Meta docs cited in issue #29 (checked there on 25 Oct 2026). sergebulaev/instagram-skills was also compared; where the two disagreed (it still lists 30 hashtags and 3-minute reels) we went with the Help Center.

- **Sends** were "the strongest signal you can earn" (`ig-audit`, `ig-carousel`). Mosseri named watch time, likes and sends as the top three, with sends counting a little more for reaching non-followers. Reworded to say that.
- **Reel length** (`ig-reel`): reels can run to 20 minutes, but Instagram doesn't recommend reels over 3 minutes to new audiences. It said 3 minutes was the limit.
- **Safe zones** (`ig-reel`): Instagram publishes none for organic posts. The 230 / 1440 / 230 numbers had no source; replaced with the ads guide's figures (top 14%, bottom 35%, 6% each side), labelled as such. `ig-story`'s y=250 / y=1600 was left as it was: nothing we found says it's wrong.
- **Hashtags** (`ig-caption`): the 5-tag cap is now in the Help Center. Mosseri's "hashtags don't increase reach" was dated February 2025; the earliest primary source is a March 2022 Stories Q&A.
- **Caption cut** (`ig-caption`, `caption.py`): 125 characters is Meta's recommended length for feed ad text, not an organic spec; the feed shows about two lines. The linter keeps 125 as a stand-in and now says so.
- **Photo shape** (`ig-carousel`): 3:4 (1080x1440) is now accepted alongside 4:5. Carousels: 20 in the app, 10 through the API.
- **Keyword auto-DMs** (`ig-dm`, `ig-story`, README): the sanctioned route is the Private Replies API, one reply per comment within 7 days, more only after the person answers. Instagram's own keyword auto-reply is only being tested on ads. It said "Instagram's own tools or an approved partner".
- **Publishing API** (README): since July 2024 it doesn't need a linked Facebook Page, and app review only applies to accounts you don't own.

## What we added

- **Your browser stays yours** (`ig-viral`, README). It used to tell Claude to drive whatever browser it had, in the user's logged-in Instagram. Now the user pastes the numbers by default; Claude reads their browser only if they ask in the chat, after a one-line note that it's a grey area under Instagram's terms.
- **Text from other people is data** (`ig-viral`, `ig-reply`, `ig-comment`, `ig-dm`). Captions, comments, bios, transcripts and DMs are read and quoted, never obeyed: no following directions in them, no letting them change what goes out, no treating them as approval, no widening what Claude does, and a one-line flag when text seems aimed at an AI. Adapted in our own words from sergebulaev/instagram-skills (MIT, Copyright (c) 2026 Sergey Bulaev); his notice is added to `LICENSE` after Jake's, which is unchanged. Nothing else was taken from that repo: its niche research runs on Apify scrapers.
- **With ChatPlace** (`ig-viral`, `ig-dm`, README), only when the ChatPlace connector is in the chat. `/ig-viral` adds accounts to Virale, takes each account's median from `virale_videos_list` and Virale's breakdown of each reel from `virale_videos_get`, checking the balance and asking before it spends credit. `/ig-dm` writes the keyword flow, shows it, and builds it with `automations_quick_setup` only on a yes, on the exact word, after checking nothing else answers that word. It keeps Jake's "the thing first, no gate" rule and says what a follow check costs if the user wants one. Without the connector, nothing changes.
- **Credit**: a "Based on…" line at the top of the README and a fuller credit at the bottom, naming the PR authors.

## Left as Jake had it, worth knowing

- `/ig-viral`'s optional YouTube Shorts step uses `yt-dlp`, which needs installing and is also against YouTube's terms if you read them strictly. It's optional and we didn't change it.
- `plugin.json` keeps Jake as the plugin's author. Its homepage and repository, the marketplace owner and the README's install commands point to this fork, and the version is 1.1.1 (his was 1.0.0).
- Not touched: the Spanish, Korean and Turkish translation PRs, the new hook formula PR (#65), the ChatPlace-style keyword PR (#35), and the carousel renderer and research scripts in #67.

## Later fixes

### 17 Nov 2026: numbers said as words count in `/ig-human` too

- `detect.py`'s SPECIFICITY check counted only digits and names. A script written the way it's said ("five hours", "twenty minutes", "four things") had nothing concrete in it, and since `/ig-reel` sends every script through `/ig-human`, every spoken script lost points for it. `hookscore.py` has counted number words since Jake's first version and `beats.py` since #5; `detect.py` never did. Found by installing the skills from the README and running `/ig-reel` end to end.
- It now counts the same number words and money words as those two. A number said in several words ("twenty-five thousand") counts once, the way "25,000" matches once, so a spelled-out script doesn't score higher than the same script in digits.
- Checked on a seven-line test script: written with number words it went from SPECIFICITY 0 to 100 and from a human score of 40.6 (FLAGGED) to 68.1. The same script in digits stays at 65.3.
- The word lists are copied into `detect.py`, not imported from `ig-reel`, because each skill folder has to work when it's installed on its own. The new test, `tests/test_spoken_numbers.py`, fails if the three copies drift apart, and checks that the spelled-out and digit versions of a script score the same.
- Version 1.1.1.
