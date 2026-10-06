---
name: trump-truth-korea-steel-analysis
description: Research, verify, and analyze Donald J. Trump's @realDonaldTrump Truth Social posts containing Korea or Steel, with reproducible topic, frequency, Korea-context, policy, and related-industry breakdowns. Use for historical or recurring monitoring of these terms; do not silently broaden the corpus to speeches or other social platforms.
---

# Trump Truth Korea/Steel Analysis

Build an auditable corpus first, then analyze it. The result must let the reader trace every claim and count back to individual posts.

## Scope before collection

Unless the user specifies otherwise:

- Analyze `@realDonaldTrump`, whose display name is Donald J. Trump. Do not identify the account by display name alone.
- Use the period from the account's first available Truth Social post through the collection cutoff. State the exact cutoff date and timezone.
- Define the **core corpus** as posts whose authored body contains the case-insensitive whole word `Korea` or `Steel`: `(?i)\b(?:korea|steel)\b`.
- Treat posts matching both keywords as one post in the union, but include them in both per-keyword counts and report the overlap.
- Keep **expanded matches** separate: matches found only in image/OCR text, video transcripts, quoted or reTruthed text, link previews, or variants such as `Korean`, `ROK`, `DPRK`, `Seoul`, `steelmaker`, and `steelmaking`.
- Separate original posts, replies, quotes, and reTruths. A reTruth is not Trump's authored wording.
- Do not add speeches, press remarks, X posts, White House releases, or news quotations unless the user requests a cross-channel study.

If the user asks for a different definition, preserve their definition and record it in the methods section.

## Collect and verify

Use direct Truth Social pages as the primary evidence. Because the site requires JavaScript and historical or deleted posts may be difficult to retrieve, use this source order:

1. Official Truth Social profile and canonical post URLs: `https://truthsocial.com/@realDonaldTrump`
2. Trump’s Truth searchable archive for discovery, deleted-post preservation, image descriptions, and video transcripts: `https://www.trumpstruth.org/`
3. Another reputable archive only to fill documented gaps or cross-check results.

The archive is a discovery and preservation aid, not proof of authorship by itself. When possible, retain both the canonical Truth Social URL and archive URL. Label deleted or inaccessible originals explicitly. Do not bypass authentication, anti-bot controls, rate limits, or site terms.

Search `Korea` and `Steel` separately, use the full date range, include removed posts when the archive supports it, and exhaust pagination. Run expanded searches separately only after completing the core set. Record the query, date range, result count, collection time, source, and any inaccessible pages.

Normalize collected rows using [references/corpus-schema.md](references/corpus-schema.md). Preserve source text verbatim in the data; put translations and interpretations in separate fields. Use America/New_York as the source-time convention when the archive specifies it, and add Asia/Seoul for Korean readers without overwriting the original timestamp.

## Clean without erasing behavior

- Deduplicate exact records by `post_id` or canonical URL.
- Keep deliberate reposts as separate posting events for activity-frequency analysis.
- Also compute a unique-message view using normalized-text hashes, so repeated messaging is visible rather than accidentally removed.
- Strip HTML only into a derived plain-text field; retain the raw source text.
- Mark whether a keyword occurs in authored body, quoted/reTruthed text, image text, video transcript, or link preview.
- Manually inspect boundary cases, especially screenshots, truncated posts, shared articles, and archive-only records.

## Classify

Read [references/taxonomy.md](references/taxonomy.md) before labeling. Apply multiple topic and industry labels when warranted; therefore, multi-label percentages may sum to more than 100%. For each post, capture:

- keyword cohort and match surface
- Korea context: South Korea, North Korea, both, peninsula/general, ambiguous, or not applicable
- topic, policy instrument, and related industries
- stance/tone, distinguishing description from interpretation
- named entities and key co-mentioned terms
- confidence and a short evidence note for non-obvious labels

Do not infer an industry merely because a company is famous for it; the post must provide a defensible connection.

## Aggregate reproducibly

Use `scripts/analyze_posts.py` for deterministic matching, duplicate views, and tables once the corpus is in CSV, JSON, or JSONL form:

```powershell
python scripts/analyze_posts.py INPUT --output-dir OUTPUT
```

If `topics` or `industries` are absent, the script supplies a rule-based baseline. Review those labels in context before treating them as final. Semicolon-delimit manually reviewed multi-label fields and rerun the script.

Always report both:

- posting events, which retain repeated posts
- unique messages, which collapse normalized exact-text repeats

For frequency charts, show raw counts and the relevant denominator. Do not claim a share of all Trump posts unless the denominator covers the same period, source, and post types.

## Deliverable

Write the final analysis in Korean unless the user requests another language. Include:

1. Executive findings, separating measured results from interpretation.
2. Scope and method: handle, exact keyword rule, expanded rule if used, date range, cutoff, timezone, sources, post types, deletion handling, and limitations.
3. Corpus overview: union count, Korea count, Steel count, overlap, expanded-only count, original/reTruth split, deleted/archive-only count, and unique-message count.
4. Time analysis by year and month, highlighting bursts with post-level evidence rather than speculating about causes.
5. Topic, Korea-context, policy-instrument, related-industry, stance, and co-mention analysis.
6. A concise interpretation of how Korea and steel are framed together or differently over time.
7. An evidence table with date, short excerpt, classifications, canonical URL, and archive URL.
8. Data-quality limitations and a reproducibility note naming the saved corpus and output files.

Link every quoted or pivotal post. Keep direct quotations short. When explaining a spike or policy context using outside reporting, browse current primary or authoritative sources and cite those separately from the post corpus.

## Quality gate

Before delivery, verify that:

- the account handle is correct and the cutoff is explicit;
- core and expanded results are not mixed;
- `Korea OR Steel`, per-keyword counts, and overlap reconcile;
- posts matching both terms are not double-counted in union totals;
- event and unique-message counts are both labeled;
- original posts and reTruths are distinguishable;
- multi-label totals are not presented as mutually exclusive;
- every key finding has traceable post evidence;
- archive gaps, deleted posts, inaccessible originals, OCR/transcript uncertainty, and possible collection incompleteness are disclosed.
