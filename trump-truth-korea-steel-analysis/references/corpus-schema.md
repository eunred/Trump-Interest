# Corpus schema

Use one row per posting event. UTF-8 CSV, JSON array, and JSONL are supported by the bundled analyzer.

## Required fields

| Field | Meaning |
|---|---|
| `post_id` | Truth Social status ID. If unavailable, create a stable archive-derived ID and explain it. |
| `created_at` | ISO 8601 timestamp with offset when available. |
| `content` | Verbatim authored post body. Keep quoted/reTruthed or media text in separate fields. |
| `canonical_url` | Official Truth Social post URL when known. |

## Recommended source and provenance fields

| Field | Meaning |
|---|---|
| `archive_url` | URL of the archive record. |
| `source` | `truthsocial`, `trumpstruth`, or another named source. |
| `collected_at` | ISO 8601 collection timestamp. |
| `post_type` | `original`, `reply`, `quote`, `retruth`, or `unknown`. |
| `is_deleted` | Boolean or `true`/`false`. |
| `raw_html` | Raw HTML when lawfully available. |
| `quoted_content` | Text written by another account or quoted post. |
| `media_text` | OCR or archive image-description text. |
| `video_transcript` | Transcript of attached video. |
| `link_preview` | Headline or preview text from a shared link. |

## Derived and reviewed fields

| Field | Meaning |
|---|---|
| `content_plain` | Plain-text rendering derived from `content`. |
| `match_scope` | `core`, `expanded_only`, or `none`. |
| `match_surface` | Semicolon-delimited: `authored_body`, `quoted_content`, `media_text`, `video_transcript`, `link_preview`. |
| `keywords` | Semicolon-delimited matched keyword families. |
| `korea_context` | Controlled value from the taxonomy. |
| `topics` | Semicolon-delimited reviewed topic labels. |
| `policy_instruments` | Semicolon-delimited reviewed policy labels. |
| `industries` | Semicolon-delimited reviewed industry labels. |
| `stance` | Primary stance/tone label. |
| `entities` | Semicolon-delimited named entities. |
| `confidence` | `high`, `medium`, or `low`. |
| `evidence_note` | Short reason for non-obvious classifications. |

## Counting invariants

- `post_id` defines a posting event.
- A normalized-content SHA-256 hash defines an exact unique message. Normalize HTML, whitespace, Unicode, and case, but do not paraphrase.
- A post containing both terms contributes once to the union and once to each keyword subtotal.
- Core membership is based only on the authored body. Expanded surfaces never change the core count.
- A repost is retained as an event even if its unique-message hash matches an earlier post.
- If timestamps lack an offset, record the source's stated timezone before conversion. Trump’s Truth states that its timestamps use America/New_York.
