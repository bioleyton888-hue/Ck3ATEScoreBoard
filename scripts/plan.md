# ATE Scoreboard — Implementation Plan

Status as of 2026-09-04.

**Built:** the "Legacy Scoreboard" button on the game-over screen opens an overlay showing the dynasty's score, a "you surpassed House X" headline, and a 15-rung ladder — each rung with its coat of arms, threshold, house and title, styled by whether it was beaten, with the house's history as a hover tooltip.

**Verified in-game: COMPLETE and working (2026-09-04).** The full panel renders — score, headline band, 16-rung ladder with heraldry, hover tooltips, and the player's own arms. This confirms the two risky pieces held: the GUI→script bridge (`MakeScope.ScriptValue`) evaluates correctly even with the player character dead, and all 45 inlined `CFixedPoint` comparisons parse.

**Remaining:** nothing required. Optional polish only — see the bottom of this file.

---

## Verified engine facts

These were checked against the CK3 1.19 game files, not assumed:

| Question | Answer |
|---|---|
| Can GUI compare a dynasty's renown to a number? | **Yes** — `GreaterThanOrEqualTo_CFixedPoint( Dynasty.GetPrestige, '(CFixedPoint)1000' )` |
| Can GUI pick text conditionally? | **Yes** — `SelectLocalization( <bool>, 'KEY_A', 'KEY_B' )` |
| Can GUI fetch a dynasty by key (e.g. House Talanque)? | **No** — no `GetDynasty('key')` global exists |
| Can GUI fetch a character by key? | **No** — no `GetCharacter('key')` global exists |
| What does a CoA widget need? | A live `Dynasty` datacontext (`coa_dynasty_widget` = `visible = "[Dynasty.IsValid]"`) |
| Does script run at game over? | **No** — the player character is dead, `trigger_event` silently fails. This killed the first implementation. GUI-only is the rule for this screen. |

**Consequence:** the overlay can only render the CoA of a dynasty it can reach through a datacontext chain. Right now that is just the player's own (`SuccessionEventWindow.GetDeadCharacter.GetDynasty`). The 15 historical houses are *not* reachable.

---

## Feature 1 — "You surpassed House X" description

**Goal:** instead of a flat list, show `"With 60 Renown you surpassed House Tagötöka, High Chieftains of the Northern Basin — <description>"`.

**Feasible today, no blockers.**

Approach: replace the single `ATE_SCOREBOARD_LIST` text block with a chain of nested `SelectLocalization` calls (or 15 stacked `text_multi` widgets each with its own `visible` condition) keyed on `Dynasty.GetPrestige` against each threshold. Highest matching tier wins — same first-match-wins logic the old event's `first_valid` used.

Each tier needs two loc keys:
- `ATE_SB_<house>_SURPASSED` — the "you surpassed…" line plus the house's description (descriptions already written in `ck2_ate_scoreboard.md`)
- a "fell short" variant for houses above the player, if we want to show those greyed rather than hidden

Design decision to make: show **only** the highest house surpassed, or the **full ladder** with everything below the player marked as beaten and everything above marked as out of reach. The ladder is closer to CK2's actual screen.

---

## Feature 2 — Show dynasty CoA and titles

**Blocked as originally specified.** GUI cannot reach the 15 historical dynasties, so their real in-game CoAs cannot be rendered dynamically.

Three ways forward:

**Option A — Static images (CHOSEN), generated automatically from ATE's own definitions.**
Pre-render each of the 15 CoAs to an image shipped under `gfx/interface/ate_scoreboard/`, drawn with a plain `icon = { texture = "..." }`. Reliable, no engine limits, tooltips trivial.

**No manual screenshotting required — we can render them ourselves from ATE's CoA definitions.** Verified feasible:

| Requirement | Status |
|---|---|
| ATE CoA definitions readable | ✅ e.g. `house_california_talanque` in `ATE_dynasties_california.txt` — pattern, colours, emblems, positions, scales |
| Source textures on disk | ✅ `game/gfx/coat_of_arms/patterns/` and `/colored_emblems/` |
| Named colour → RGB mapping | ✅ `game/common/named_colors/default_colors.txt` (hsv/rgb values) |
| DDS readable by tooling | ✅ PIL 12.2.0 opens them as RGBA |
| Colour encoding understood | ✅ see below |

**Colour model (confirmed by inspecting pixel data):** each texture's R/G/B channels are masks selecting `color1`/`color2`/`color3`, with alpha defining shape. `pattern_vertical_split_01.dds` contains exactly two values — `[255,0,0]` (colour 1) and `[255,255,0]` (colour 2). `ce_sun.dds` uses R as its primary mask with alpha for the silhouette.

### ✅ BUILT — `scripts/render_coas.py`

Parses the CoA blocks, resolves named colours, composites pattern + emblems honouring `position` / `scale` / `depth`, writes one PNG per house into `gfx/interface/ate_scoreboard/`. Re-runnable at any size: `python scripts/render_coas.py --size 128`.

**Result: 11 of 15 rendered from ATE's real definitions, 4 placeholders, 0 failures.**

**Output format:** PNG. Confirmed CK3 accepts it — the base game ships 248 `.png` files under `gfx/interface` and references them straight from `.gui`. No DDS conversion needed.

**Two engine behaviours discovered while building it** (both found by rendering and looking, not by assumption):

1. **`depth` is inverted from what you'd expect — higher depth draws FURTHER BACK.** Caught on `dynn_california_tagotoka`, whose depth-17 full-canvas block otherwise covers the entire shield. Emblems must be drawn in *descending* depth order.

2. **Patterns and emblems use completely different colour encodings.**
   - *Patterns* mask colour slots in RGB: `pattern_vertical_split_01.dds` holds exactly `[255,0,0]` (colour 1) and `[255,255,0]` (colour 2).
   - *Emblems* are alpha silhouettes. Every emblem checked (`ce_sun`, `ce_antlers_attire`, `ce_block_02`, `ce_circle_mask`, `ce_buddhist_moon`) reads **R~0, G~0, B~128** on opaque pixels — that B~128 is a neutral baseline, *not* a colour-3 mask. Treating it as one blended every emblem halfway to grey and washed out the entire first render pass.

**The four placeholders** — Jacaranda, Clinton, Nokona and Yoder — have **no authored CoA anywhere in ATE or the base game**. Their dynasty keys (`dynn_Jacaranda`, `dynn_Clinton`, `dynn_Nokona`, `dynn_Yoder`) are plain name-list entries, so CK3 generates their heraldry procedurally at runtime and it differs per playthrough. There is nothing canonical to extract. Options: author our own CoA definitions for these four, or keep the neutral placeholder shield.

**Not implemented:** `mask = { N }` (clips an emblem to a pattern region — affects Talanque's moon slightly). Negative `scale` mirroring *is* handled. Output is not pixel-identical to the game's renderer, but all 11 read correctly as their intended designs.

**Option B — Player CoA only.**
Show only the player's own house CoA at the top next to their score, and leave the 15 as text. Zero art cost, works immediately, but loses most of the visual comparison.

**Option C — Reuse existing frame art.**
Use a generic shield/frame icon per row instead of real CoAs. Cheap, but visually weak.

**Titles:** the title text next to each house ("Emperors of California", etc.) is just localisation and is already written — no constraint there. Only the heraldry is blocked.

---

## Feature 3 — Hover CoA for the description

**Feasible once Feature 2 is resolved.** Any widget takes `tooltip = "KEY"`, so whichever element represents a house (static CoA image, frame icon, or the row itself) can carry that house's description as a hover tooltip.

This pairs naturally with Feature 1: if the ladder shows short one-line entries, the full lore description from `ck2_ate_scoreboard.md` lives in the tooltip instead of cluttering the panel.

---

## Feature 4 — Reconfigure the points ✅ DONE

**Outcome: the thresholds did not need to change at all. The CK2 board carries over verbatim.**

Instead of hand-tuning numbers against guesswork, the score formula was made *exact*, and the original CK2 thresholds turned out to fit it almost perfectly.

CK3 prices each legacy perk from two defines (`00_defines.txt:1031-1032`):

```
COST = PERK_COST_BASE + (unlocked perks * PERK_COST_MULTIPLIER)   # 250 + 500n
```

Summing that series over N perks gives a closed form:

```
total renown ever spent = SUM(250 + 500i, i=0..N-1) = 250N + 500*N(N-1)/2 = 250 * N^2
```

Verified exactly against the game's own curve for N = 1, 2, 3, 5, 10, 15, 20, 25. So lifetime renown is reconstructed precisely as:

```
score = current renown + 250 * perks^2
```

**Resulting ladder placement** (leftover renown ignored):

| Perks | Score | Rung reached |
|---|---|---|
| 2 | 1 000 | Avondale (bottom) |
| 4 | 4 000 | Soady |
| 6 | 9 000 | Yoder |
| 8 | 16 000 | Castel |
| 10 | 25 000 | Mahonic |
| 12 | 36 000 | Nokona |
| 15 | 56 250 | Abbas |
| 18 | 81 000 | Royall |
| 20 | 100 000 | Talanque (top) |

A smooth spread across all 15 rungs, with 20 perks for the summit — demanding but reachable in a long successful game. This is why the CK2 thresholds were kept unchanged.

**Note on the earlier 60-renown reading:** that was taken at the 2666 start date, not the end of a run, so it was a starting value rather than an endgame score. It is not evidence of miscalibration.

Still worth confirming against a real finished game once one is available.

---

## Underlying issue — the scoring metric itself

The 60 Renown reading exposed a design bug, not just bad numbers.

**`Dynasty.GetPrestige` returns the *current unspent* renown balance, not lifetime achievement.** Renown is the currency you spend on dynasty legacies, so a player who bought many legacies shows a *low* score despite a great dynasty. Ranking on it punishes exactly the players who played well.

**Available `Dynasty.*` GUI functions** (verified present in CK3 1.19):

| Function | Use |
|---|---|
| `GetPrestige` | Current unspent renown |
| `GetNumberOfLegacies` | **Legacies purchased — recovers the "spent" renown** |
| `GetPrestigeLevelName` | Rank name ("Illustrious" etc.), never decreases |
| `GetPrestigeLevelProgress` | Progress within current level |
| `GetNumberOfRulers` | Rulers the dynasty produced |
| `GetNumberOfCounties` | Land held |
| `GetNumberOfLivingMembers` / `GetNumberOfDeadMembers` | Dynasty size over time |
| `GetTotalMilitaryStrength` | Military power |
| `GetDynastyCoA` | CoA accessor (needs a live Dynasty, so no help for the 15) |

**Score formula — DECIDED: renown + legacies only.**

```
score = GetPrestige + ( GetNumberOfLegacies × <legacy weight> )
```

This restores spent renown so the number reflects lifetime achievement rather than leftover currency. `GetNumberOfRulers` / `GetNumberOfCounties` were considered and deliberately left out to keep it simple.

Computable entirely in the GUI layer with `Add_CFixedPoint` / `Multiply_CFixedPoint`, so it still works with the player dead.

---

## Decisions made

- **Score formula:** renown + legacies only. No rulers/counties.
- **Points reconfiguration:** thresholds hand-set directly, no scale-factor equation. Deferred to step 2.
- **CoA approach:** static images for all 15 houses, **generated automatically** by a script from ATE's own CoA definitions. No manual capture.
- **Comparison style:** full ladder — show all 15, surpassed houses marked as beaten, houses above marked out of reach.

## Progress

1. ✅ **Score formula** — moved into a script value; counts spent renown, not just leftover
2. ✅ **Feature 4** — formula made exact (`250 * perks^2`); CK2 thresholds kept unchanged
3. ✅ **Feature 1** — full ladder with per-tier surpassed/missed text and a headline band
4. ✅ **Feature 2** — coats of arms on every rung, all 15 rendered from ATE's definitions
5. ✅ **Feature 3** — each CoA carries its house description as a hover tooltip
6. ✅ **Player's own CoA** at the top beside the score, via `coa_dynasty_medium`
7. ✅ **House Ramsesovich** added at a flat 500, below the CK2 board, rendered from the Neomoor mod

**All features complete and confirmed working in-game.**

## Optional polish

Nothing here is required — the mod works as intended.

- Three houses show their realm's arms rather than their own (Jacaranda → `k_mexico`,
  Nokona → `k_comancheria`, Yoder → `k_dutchland`), since those houses have no dynasty CoA
  anywhere in ATE. One line each in `HOUSES` to change.
- `mask = { N }` is unimplemented in the renderer; only visibly affects Talanque's moon,
  which renders as a flat grey disc over the sun rather than being clipped.
- Thresholds are the CK2 board verbatim and have not been tested against a genuinely long
  playthrough. If 20 perks proves too easy or too hard for the summit, the numbers are
  one edit per rung in the `.gui` file.
