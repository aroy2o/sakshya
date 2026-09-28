# CLASSIFIER_BENCHMARK.md — real-photo classifier accuracy (Reality Pass R5)

Companion to `docs/REAL_DATA_PLAN.md` §8's R5 row: *"Real-photo benchmark: ≥20 CC-licensed real photos (record URL, author, licence per file), run the current Ollama model and one alternative, write `docs/CLASSIFIER_BENCHMARK.md` with a confusion matrix, expose measured accuracy via API. Never quote accuracy from the AI-generated set as real-world accuracy."*

**This document reports accuracy on REAL, publicly-sourced photographs — not on the AI-generated synthetic photo set used elsewhere in this project.** See §5 for why that distinction is load-bearing.

**TL;DR:** 45 real CC-licensed photos across 8/9 PRD §15.1 categories were sourced and ground-truth-labelled (§1-2). `moondream` (production default) was run against all 45: it scored 6.7% "accuracy", but that number is an artifact — 100% of its raw responses failed structured-output validation under the neutral (no-declared-category) prompt this benchmark requires, so the result measures schema reliability, not classification skill (§4.1). `llava` was tried as the alternative model; a single test call pushed this machine's swap to 100% full, so it was run on a bounded 9-photo stratified sample instead of the full set — it produced cleaner JSON when it completed (3/3 valid vs. moondream's 0/45) but 6 of 9 attempts hit Ollama connection timeouts under memory pressure before finishing (§4.2). **Net finding: this pass could not cleanly measure either model's real classification accuracy — it surfaced a structured-output-reliability gap for moondream and a hardware-headroom limit for llava, both reported honestly rather than papered over.**

---

## 1. Dataset

45 real, CC-licensed photographs hand-picked from Wikimedia Commons, one file at a time (not a bulk category crawl — `scripts/fetch_real_benchmark_photos.py`'s `CURATED_PHOTOS` list is a fixed, reviewed set of exactly the files used; re-running the script re-downloads the same list, it does not crawl further). Every file's source URL, author, and exact per-file licence is recorded in `scripts/real_photos/manifest.json` and summarized in `docs/DATA_SOURCES.md`'s "Photo/classifier benchmark" section.

| Ground truth category | Count | Commons source |
|---|---|---|
| SM — Structural measures | 10 | Category:Check dams in India, Category:Check dams in Kerala |
| PT — Pond–Tanks | 6 | Category:Ponds in India |
| BN — Bunds | 5 | Category:Levees in India (Baitarani river embankment restoration series, Odisha) |
| AM — Agronomic measures | 5 | Category:Agricultural terraces in Kerala |
| VM — Vegetative measures | 3 | Category:Reforestation in India |
| LS — Livestock | 3 | Category:Goats in Assam / India (goat-shed photos) |
| LH — Livelihood | 5 | Category:Sericulture in India, Category:Fish farming in India |
| NC — Nala–Channels | 5 | Category:Irrigation canals in India (small/village-scale only) |
| OM — Others | 0 | **Not sourced** — see §6 |
| NONE (deliberate distractor) | 3 | Category:Street markets in India, Category:Buses in Assam |
| **Total** | **45** | |

8 of the 9 PRD §15.1 categories are represented with real photos (broader than the plan's named starting point of "Check dams" alone), plus 3 deliberate off-topic distractors to test whether the classifier over-predicts a category on a scene that shows none of them.

Licence mix across the 45 files (never assumed uniform — checked per file via the Commons API's `extmetadata`): CC BY-SA 4.0 (24), CC BY-SA 3.0 (10), CC BY 3.0 (6), CC0 (2), Public domain (1), CC BY-SA 2.0 (1), CC BY 4.0 (1).

## 2. Ground truth methodology

These are not SAKSHYA field records — there is no "declared activity" to check a photo against. Ground truth was assigned by hand at curation time: **"which of the 9 PRD §15.1 categories (or none) does this photo genuinely depict?"** — based on the Commons category it was filed under plus a manual read of its title/description, with anything ambiguous or miscategorized excluded rather than force-fit (see `scripts/fetch_real_benchmark_photos.py`'s module docstring for specific exclusions: a named reservoir dam wrongly filed under "Check dams", five unrelated tourism photos wrongly filed under "Levees", major state-infrastructure canals excluded from the NC set as a different scale from a watershed-programme channel).

This is a **single-rater** ground truth (the vision-ai-engineer agent that curated the set), not independently cross-checked by a second annotator — a real limitation for a formal benchmark, disclosed here rather than glossed over.

## 3. Classification protocol

The exact same production code path is used as everywhere else in SAKSHYA (`services/vision_classifier.VisionClassifierService` + `services/vision_providers/ollama_provider.OllamaVisionProvider`) — no bespoke one-off prompt was written for this benchmark. `scripts/run_real_photo_benchmark.py` calls `service.classify()` on each photo.

Because these photos have no real declared activity, each is classified with a **neutral declared label** rather than the ground truth (to avoid trivially anchoring the model's answer onto the value being scored against):

- `declared_category = "UNKNOWN"`
- `declared_activity = "a general rural or agricultural scene"`

The scored output is `predicted_category` from the model's own response, not `matches_declared` (which only means something against a real declared activity — it is recorded in the raw results but is not part of this benchmark's accuracy metric). Ground truth `"NONE"` is scored as correct only when the model predicts `"UNKNOWN"` (its own "doesn't look like any of the 9" escape hatch).

**A methodological finding worth stating plainly:** an earlier version of the neutral `declared_activity` string used parenthetical meta-commentary ("unspecified activity (real-photo benchmark — no declared label provided)"). Under that wording, moondream's first 5 responses all failed Pydantic schema validation (e.g. it echoed `predicted_category="unspecified"`, a word from the prompt, instead of picking one of the fixed enum values) and were degraded by `VisionClassifierService`'s designed fallback to an honest `UNKNOWN`/0.0-confidence result rather than a guess. A direct side-by-side test on the same photo — the confusing neutral prompt vs. a real `declared_category="SM"` + a short declared activity — confirmed this was prompt wording, not a transient/resource issue: the real-declared-category call returned a clean, schema-valid response. The wording was shortened to the plain phrase above before the full run below, and the 5 affected responses were discarded and reclassified under the new wording (not mixed into the results). This is disclosed because it is itself informative: **moondream's structured-output reliability is measurably more fragile without a category anchor in the prompt than production usage (which always supplies a real declared_category) would suggest.**

## 4. Results

### 4.1 moondream (current production default, `~1.7GB`, `moondream:latest`)

**Measured on the full 45-photo set. Accuracy: 3/45 = 6.7%.**

**Headline finding: 45/45 (100%) of moondream's raw responses failed Pydantic schema validation** under the neutral-prompt condition (§3) and were degraded by `VisionClassifierService`'s designed fallback to `predicted_category="UNKNOWN"`, `confidence=0.0` — never a guessed category (CLAUDE.md "never fabricate a guess" working exactly as intended). Concretely this means: every one of the 42 real-category photos scored as incorrect (ground truth ≠ `UNKNOWN`), and all 3 of the deliberate `NONE` distractors scored as *technically* correct — not because moondream recognized them as off-topic, but because every single response degraded to the same fallback value regardless of what the photo showed. **The 6.7% figure should be read as "3/45 happened to be scored correct by a mechanism that produces the same output for every photo," not as "moondream correctly identified 3 photos" — treat it as effectively unmeasured classification ability, not a low-but-real accuracy.**

The two observed failure modes (see `scripts/real_photos/benchmark_results_moondream.json` for the raw `ai_result.evidence` on every entry):
- Echoing a word from the prompt into `predicted_category` instead of a fixed enum value (seen with an earlier, more verbose neutral-prompt wording — see §3's methodology note; not present in the final run below, whose failures were different).
- An empty `evidence` string, failing the schema's `min_length=1` requirement, even when every other field (including a valid `predicted_category` enum value) was well-formed.

Confusion matrix (rows = ground truth, columns = predicted; `NONE` ground truth and `UNKNOWN` predicted share one axis label, see `scripts/run_real_photo_benchmark.py::gt_to_axis`):

| Ground truth ↓ / Predicted → | UNKNOWN |
|---|---|
| SM (n=10) | 10 |
| PT (n=6) | 6 |
| BN (n=5) | 5 |
| AM (n=5) | 5 |
| VM (n=3) | 3 |
| LS (n=3) | 3 |
| LH (n=5) | 5 |
| NC (n=5) | 5 |
| NONE (n=3) | 3 |

Every cell outside the `UNKNOWN` column is zero — the matrix is degenerate (single-column) precisely because of the 100% schema-invalidity rate above, not because the model consistently and deliberately called everything "none of the 9."

**Contrast with production usage:** `scripts/batch_classify.py`'s run against the AI-generated synthetic set (§5), which always supplies a real `declared_category`, got 18/18 clean matches with zero schema-validation failures reported. The gap between "0% schema failures with a declared-category anchor" and "100% schema failures without one" is the single most important, demo-relevant finding of this benchmark: **moondream's structured-output reliability depends heavily on being handed a specific category to confirm/deny (an easier "verify this" task) — it is not currently reliable at open-set "which of these 9 is this" classification from a photo alone.** This is a real production risk if SAKSHYA ever needs a model to classify a photo with no declared activity (e.g. auto-tagging an unlabelled upload), even though it does not affect the current `POST /assets/{id}/classify` flow, which always has a real declared category from the field record.

### 4.2 llava (`~4.9GB`, `llava:latest`, alternative model tested)

**Measured on a stratified sample of 9 photos (one per ground-truth category actually present — OM has none, see §1), not the full 45.** RAM headroom was checked first per this task's own instruction: this machine has ~15GB total, and a single test call before committing to a full run pushed swap usage to 100% (8.0/8.0GB) even for one image. Running the full 45-photo set at that resource cost (observed ~90-240s/photo, i.e. potentially over an hour pinning the shared machine — which also runs the other Reality-Pass agents' work and the human's desktop — at its memory ceiling) was judged too risky; a bounded, still cross-category sample was run instead. **Accuracy: 1/9 = 11.1% — but, as with moondream, this number is not a clean read on classification ability; see the breakdown below.**

Of the 9 photos attempted, two genuinely different things happened:

- **3 photos (SM, PT, BN) got real, well-formed, content-based responses** with non-zero confidence (0.20, 0.50, 0.20) and specific evidence text (e.g. "*The image shows a body of water with a reflection... the image is not clear enough to confidently determine the specific activity*"). llava correctly and honestly reported low confidence / `predicted_category="UNKNOWN"` on all three rather than guessing — arguably **better-calibrated behavior than moondream's schema-garbling** on the same neutral-prompt task, even though it didn't land on the correct category either.
- **6 photos (AM, VM, LS, LH, NC, and the one NONE distractor sampled) failed with an Ollama connection timeout** (`HTTPConnectionPool(...): Read timed out`), both retry attempts, ~240s elapsed each — a genuine resource-exhaustion event, not a reflection of llava's classification ability. `ollama ps` confirmed the runner had spilled from 100% GPU onto a 34%/66% CPU/GPU split under memory pressure by that point, consistent with swap being fully saturated (`free -h`: 8.0/8.0GB swap used). These 6 are indistinguishable in `predicted_category`/`confidence` from a genuine "doesn't know" — but their `ai_result.evidence` field starts with `"Classifier response invalid after 2 attempt(s): Ollama request failed..."`, not model-generated text, which is how they're told apart in `scripts/real_photos/benchmark_results_llava.json`.

The single "correct" result (the one `NONE` distractor sampled) is itself one of the 6 timeout failures, not a genuine detection — llava never actually looked at that image long enough to answer. **Read this section as: llava was more reliable at producing valid, honestly-calibrated JSON when it did complete (3/3 clean responses, 0 schema violations, vs. moondream's 0/45), but this machine could not sustain it running long enough to get a real read on its classification accuracy.** A fair llava-vs-moondream accuracy comparison would need either more RAM/a lighter llava quantization, or running on a less memory-contended machine — not attempted further here per this task's own "check RAM headroom, don't force a rushed second run" guidance.

Confusion matrix (rows = ground truth, columns = predicted, n=9 stratified sample):

| Ground truth ↓ / Predicted → | UNKNOWN | Outcome |
|---|---|---|
| SM (n=1) | 1 | genuine low-confidence response (conf 0.20) |
| PT (n=1) | 1 | genuine low-confidence response (conf 0.50) |
| BN (n=1) | 1 | genuine low-confidence response (conf 0.20) |
| AM (n=1) | 1 | connection timeout |
| VM (n=1) | 1 | connection timeout |
| LS (n=1) | 1 | connection timeout |
| LH (n=1) | 1 | connection timeout |
| NC (n=1) | 1 | connection timeout |
| NONE (n=1) | 1 | connection timeout |

## 5. Critical distinction — do not confuse with the synthetic-set numbers

`scripts/batch_classify.py` reports the classifier's behavior on `scripts/generate_synthetic_photos.py`'s **AI-generated** photo set (18 good + 4 deliberately-mismatched, 22 total): 18/18 good records scored `matches=yes`, all 4 mismatches scored `matches=no`. That number describes something narrower and easier than this benchmark — it is the model's ability to notice a category swap on images the classifier itself (or a similar generator) effectively created, with declared activities handed to it as short, clean, DRISHTI-style labels.

**This document's numbers (§4) are a different, harder, and more honest measurement: real photographs, real-world noise (lighting, angle, clutter, watermarks, multiple candidate subjects in frame), and no declared label to anchor on.** The two must never be quoted interchangeably, and any dashboard or report surfacing accuracy must say which one it means. `GET /classifier/benchmark`'s response `note` field states this explicitly so a consumer of the API can't lose the distinction downstream.

## 6. Known gaps and limitations

- **OM (Others) has zero real photos.** PRD §15.1 describes OM as "jungle clearance, agro service centres" — an inherent catch-all with no matching, clearly-on-topic Commons category found in the time available. Not silently worked around; the gap is visible in both this document and `GET /classifier/benchmark`'s `dataset.categories_not_covered`.
- **Single-rater ground truth** (§2) — no second annotator cross-check.
- **Small per-category counts** (3–10 photos per category) — enough for a directional read, not a statistically tight per-class accuracy figure. Do not over-interpret a single-digit-photo category's 100%/0% score as a stable rate.
- **CPU/GPU-shared, memory-contended local inference** — each classification takes on the order of tens of seconds to several minutes per photo on this machine (moondream ~30-240s, llava ~90-240s and eventually timing out); this rules out a much larger real-photo set within the time available for this pass, and directly caused llava's run to be a 9-photo stratified sample rather than the full 45 (§4.2).
- **llava's accuracy figure is not usable as a clean model-quality signal.** 6 of its 9 attempts failed on Ollama connection timeouts under memory pressure (swap fully saturated at 8.0/8.0GB), not on llava's own classification behavior — see §4.2 for the exact breakdown. Only 3 genuine llava responses exist in this benchmark, too few to compare against moondream's (also-confounded) 6.7% in any statistically meaningful way. The one clean, repeatable comparison this benchmark does support: llava produced valid, schema-compliant JSON on 3/3 of its completed calls, moondream on 0/45 — a real difference in structured-output reliability, even though neither model's category-*accuracy* could be cleanly measured here.
- **Neither model's real classification accuracy is established by this pass.** The dominant finding for both models turned out to be an infrastructure/reliability one (schema compliance and, for llava, resource exhaustion) rather than a clean "X% of photos correctly categorized" result. This is itself the honest, reportable outcome — CLAUDE.md's "never fabricate a number" cuts the other way here too: it would be dishonest to smooth over what actually happened and present either 6.7% or 11.1% as if it reflected genuine classification skill.

## 7. Reproducing this benchmark

```bash
# 1. Download the curated real-photo set (idempotent — skips files already on disk)
python scripts/fetch_real_benchmark_photos.py

# 2. Classify with a given Ollama model (must already be pulled: `ollama pull <model>`).
#    Resumable by default -- re-running skips photos already classified for that model.
python scripts/run_real_photo_benchmark.py --model moondream

# For a heavier model on a RAM-constrained machine, bound the run to N photos per
# category instead of the full 45 (this is how the llava run in §4.2 was produced):
python scripts/run_real_photo_benchmark.py --model llava --max-per-category 1

# 3. Results land in scripts/real_photos/benchmark_results_<model>.json (per-photo)
#    and benchmark_summary_<model>.json (confusion matrix + accuracy), and are
#    served live at GET /classifier/benchmark once at least one model has run.
```
