#!/usr/bin/env python3
"""Normalize and aggregate a Korea/Steel Truth Social corpus using stdlib only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


CORE = {
    "Korea": re.compile(r"\bkorea\b", re.I),
    "Steel": re.compile(r"\bsteel\b", re.I),
}
EXPANDED = {
    "Korea": re.compile(
        r"\b(?:korea(?:n|ns)?|south\s+korea|north\s+korea|republic\s+of\s+korea|"
        r"dprk|rok|seoul|pyongyang)\b",
        re.I,
    ),
    "Steel": re.compile(
        r"\b(?:steel|steels|steelmaker(?:s)?|steelmaking|steelworker(?:s)?|steelworks)\b",
        re.I,
    ),
}
SURFACES = [
    ("authored_body", "content_plain"),
    ("quoted_content", "quoted_content"),
    ("media_text", "media_text"),
    ("video_transcript", "video_transcript"),
    ("link_preview", "link_preview"),
]

TOPIC_RULES = {
    "trade_tariffs": r"\b(?:tariff|quota|trade deficit|dumping|reciprocal|trade deal|import|export)\w*\b",
    "manufacturing_reshoring": r"\b(?:manufactur|factory|factories|plant|reshor|made in america|american jobs?)\w*\b",
    "corporate_investment_deal": r"\b(?:invest|acquisition|merger|joint venture|deal|billion|trillion)\w*\b",
    "diplomacy_negotiation": r"\b(?:summit|meet|meeting|negotiat|state visit|president|prime minister)\w*\b",
    "security_defense": r"\b(?:military|troops?|defen[sc]e|missile|nuclear|alliance|sanction|weapon)\w*\b",
    "campaign_domestic_politics": r"\b(?:election|vote|campaign|democrat|republican|biden|harris)\w*\b",
    "regulation_environment": r"\b(?:regulat|emission|environment|permit|climate|epa)\w*\b",
    "market_price_supply": r"\b(?:price|cost|shortage|capacity|supply|demand|market)\w*\b",
}

POLICY_RULES = {
    "tariff": r"\btariff\w*\b",
    "quota": r"\bquota\w*\b",
    "antidumping_countervailing": r"\b(?:dumping|anti-dumping|antidumping|countervailing)\b",
    "sanction": r"\bsanction\w*\b",
    "subsidy_tax_credit": r"\b(?:subsid|tax credit|incentive)\w*\b",
    "procurement": r"\b(?:procurement|buy american|government purchase)\w*\b",
    "investment_commitment": r"\b(?:invest|commitment|pledge)\w*\b",
    "trade_agreement": r"\b(?:trade agreement|trade deal|fta|usmca)\b",
    "diplomatic_negotiation": r"\b(?:summit|negotiat|diplomatic|meeting)\w*\b",
    "military_posture": r"\b(?:troops?|military|deployment|alliance)\w*\b",
    "regulatory_change": r"\b(?:regulat|deregulat|rule|permit)\w*\b",
}

INDUSTRY_RULES = {
    "steel_primary": r"\b(?:steel|mill|foundry|blast furnace|stainless|hot rolled|cold rolled)\w*\b",
    "automotive": r"\b(?:auto|automobile|vehicle|car|truck|suv)\w*\b",
    "shipbuilding_maritime": r"\b(?:shipbuild|shipyard|vessel|maritime|naval|submarine)\w*\b",
    "defense_aerospace": r"\b(?:defen[sc]e|weapon|aircraft|aerospace|missile|fighter jet)\w*\b",
    "semiconductors_electronics": r"\b(?:semiconductor|microchip|chip|electronics|fab)\w*\b",
    "batteries_ev": r"\b(?:battery|batteries|electric vehicle|\bev\b|lithium)\w*\b",
    "energy": r"\b(?:oil|gas|lng|energy|electricity|power plant|nuclear energy|solar|wind)\w*\b",
    "construction_infrastructure": r"\b(?:construction|infrastructure|bridge|pipeline|building|highway|rail)\w*\b",
    "mining_raw_materials": r"\b(?:iron ore|coal|scrap|mining|critical mineral|nickel|cobalt)\w*\b",
    "machinery_appliances": r"\b(?:machinery|equipment|appliance|washing machine)\w*\b",
    "logistics_ports": r"\b(?:logistics|freight|port|shipping|cargo)\w*\b",
    "finance_investment": r"\b(?:financ|capital|fund|bank|investment)\w*\b",
    "agriculture_food": r"\b(?:agricultur|farm|food|soybean|corn|beef)\w*\b",
}

STOPWORDS = {
    "about", "after", "again", "against", "also", "america", "american", "and", "are", "been",
    "being", "but", "can", "could", "did", "does", "donald", "for", "from", "great", "had", "has",
    "have", "here", "his", "into", "its", "just", "more", "most", "much", "not", "now", "our", "out",
    "over", "president", "said", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "today", "trump", "truth", "very", "was", "were", "what", "when", "where",
    "which", "who", "will", "with", "would", "you", "your", "korea", "steel",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text(value: Any) -> str:
    parser = _TextExtractor()
    parser.feed(str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", plain_text(value)).casefold()
    return re.sub(r"\s+", " ", value).strip()


def split_labels(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[;,|]", str(value or ""))
    return sorted({str(item).strip() for item in items if str(item).strip()})


def read_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8-sig") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            for key in ("posts", "items", "results"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            raise ValueError("JSON input must be an array or contain a posts/items/results array")
        return [dict(row) for row in data]
    raise ValueError("Input must be .csv, .json, or .jsonl")


def date_parts(value: Any) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return "unknown", "unknown"
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        stamp = datetime.fromisoformat(candidate)
        return f"{stamp.year:04d}", f"{stamp.year:04d}-{stamp.month:02d}"
    except ValueError:
        match = re.match(r"(\d{4})-(\d{2})", raw)
        return (match.group(1), f"{match.group(1)}-{match.group(2)}") if match else ("unknown", "unknown")


def infer_labels(text: str, rules: dict[str, str], fallback: str) -> list[str]:
    labels = [label for label, pattern in rules.items() if re.search(pattern, text, re.I)]
    return labels or [fallback]


def infer_korea_context(text: str, has_korea: bool) -> str:
    if not has_korea:
        return "not_applicable"
    north = bool(re.search(r"\b(?:north korea(?:n)?|dprk|pyongyang|kim jong[ -]?un)\b", text, re.I))
    south = bool(re.search(r"\b(?:south korea(?:n)?|republic of korea|\brok\b|seoul)\b", text, re.I))
    if north and south:
        return "both_koreas"
    if north:
        return "north_korea"
    if south:
        return "south_korea"
    if re.search(r"\bkorean peninsula\b", text, re.I):
        return "korean_peninsula_general"
    return "ambiguous_korea"


def annotate(row: dict[str, Any]) -> dict[str, str]:
    out = {str(key): "" if value is None else str(value) for key, value in row.items()}
    body = plain_text(row.get("content", row.get("content_plain", "")))
    out["content_plain"] = body

    exact_body = {name for name, pattern in CORE.items() if pattern.search(body)}
    surfaces: set[str] = set()
    expanded_keywords: set[str] = set()
    for surface_name, field in SURFACES:
        text = body if field == "content_plain" else plain_text(row.get(field, ""))
        if any(pattern.search(text) for pattern in EXPANDED.values()):
            surfaces.add(surface_name)
        for name, pattern in EXPANDED.items():
            if pattern.search(text):
                expanded_keywords.add(name)

    out["match_scope"] = "core" if exact_body else ("expanded_only" if expanded_keywords else "none")
    out["match_surface"] = ";".join(sorted(surfaces))
    out["keywords"] = ";".join(sorted(exact_body if exact_body else expanded_keywords))
    digest = hashlib.sha256(normalized_text(body).encode("utf-8")).hexdigest()
    out["content_sha256"] = digest
    year, month = date_parts(row.get("created_at"))
    out["year"] = year
    out["month"] = month

    context_text = " ".join(
        body if field == "content_plain" else plain_text(row.get(field, ""))
        for _, field in SURFACES
    )
    has_korea = "Korea" in (exact_body if exact_body else expanded_keywords)
    out["korea_context"] = str(row.get("korea_context") or infer_korea_context(context_text, has_korea))

    topics = split_labels(row.get("topics")) or infer_labels(context_text, TOPIC_RULES, "other")
    policies = split_labels(row.get("policy_instruments")) or infer_labels(
        context_text, POLICY_RULES, "none_or_unclear"
    )
    industries = split_labels(row.get("industries")) or infer_labels(
        context_text, INDUSTRY_RULES, "none_or_unclear"
    )
    out["topics"] = ";".join(topics)
    out["policy_instruments"] = ";".join(policies)
    out["industries"] = ";".join(industries)
    out["stance"] = str(row.get("stance") or "ambiguous")
    out["confidence"] = str(row.get("confidence") or "low")
    return out


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    if not materialized:
        path.write_text("", encoding="utf-8-sig")
        return
    preferred = [
        "post_id", "created_at", "year", "month", "post_type", "content", "content_plain",
        "match_scope", "match_surface", "keywords", "korea_context", "topics", "policy_instruments",
        "industries", "stance", "confidence", "entities", "evidence_note", "canonical_url", "archive_url",
        "source", "is_deleted", "collected_at", "content_sha256",
    ]
    seen = {key for row in materialized for key in row}
    fields = [field for field in preferred if field in seen] + sorted(seen - set(preferred))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def dimension_rows(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        for label in split_labels(row.get(field)) or ["unspecified"]:
            counts[(row["match_scope"], label)] += 1
    label_field = {
        "topics": "topic",
        "industries": "industry",
        "policy_instruments": "policy_instrument",
    }.get(field, field)
    return [
        {"match_scope": scope, label_field: label, "event_count": count}
        for (scope, label), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def frequency_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[row["month"]].append(row)
    result = []
    for month, group in sorted(buckets.items()):
        core = [row for row in group if row["match_scope"] == "core"]
        result.append({
            "month": month,
            "event_count": len(group),
            "core_event_count": len(core),
            "expanded_only_event_count": len(group) - len(core),
            "unique_message_count": len({row["content_sha256"] for row in group}),
            "korea_core_count": sum("Korea" in split_labels(row["keywords"]) for row in core),
            "steel_core_count": sum("Steel" in split_labels(row["keywords"]) for row in core),
            "overlap_core_count": sum(
                {"Korea", "Steel"}.issubset(set(split_labels(row["keywords"]))) for row in core
            ),
        })
    return result


def co_mentions(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    event_counts: Counter[str] = Counter()
    occurrence_counts: Counter[str] = Counter()
    for row in rows:
        tokens = [token.casefold() for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", row["content_plain"])]
        tokens = [token for token in tokens if token not in STOPWORDS]
        occurrence_counts.update(tokens)
        event_counts.update(set(tokens))
    return [
        {"term": term, "post_count": event_counts[term], "occurrence_count": count}
        for term, count in occurrence_counts.most_common(100)
    ]


def make_summary(rows: list[dict[str, str]], duplicate_input_ids: int, excluded: int) -> dict[str, Any]:
    core = [row for row in rows if row["match_scope"] == "core"]
    return {
        "matched_posting_events": len(rows),
        "core_posting_events": len(core),
        "expanded_only_posting_events": len(rows) - len(core),
        "core_korea_events": sum("Korea" in split_labels(row["keywords"]) for row in core),
        "core_steel_events": sum("Steel" in split_labels(row["keywords"]) for row in core),
        "core_overlap_events": sum(
            {"Korea", "Steel"}.issubset(set(split_labels(row["keywords"]))) for row in core
        ),
        "unique_messages": len({row["content_sha256"] for row in rows}),
        "repeated_message_events": len(rows) - len({row["content_sha256"] for row in rows}),
        "deleted_or_archive_only_events": sum(
            str(row.get("is_deleted", "")).casefold() in {"1", "true", "yes"}
            or not row.get("canonical_url")
            for row in rows
        ),
        "duplicate_input_ids_removed": duplicate_input_ids,
        "excluded_nonmatches": excluded,
        "earliest_created_at": min((row.get("created_at", "") for row in rows if row.get("created_at")), default=""),
        "latest_created_at": max((row.get("created_at", "") for row in rows if row.get("created_at")), default=""),
    }


def write_report(path: Path, summary: dict[str, Any], dimensions: dict[str, list[dict[str, Any]]]) -> None:
    lines = [
        "# Korea/Steel Truth Social corpus summary",
        "",
        "> These are deterministic corpus statistics. Rule-based labels must be reviewed in context before publication.",
        "",
        "## Corpus",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    for title, rows in dimensions.items():
        lines.extend(["", f"## {title}", "", "| Scope | Label | Events |", "|---|---|---:|"])
        for row in rows[:20]:
            label_key = next(key for key in row if key not in {"match_scope", "event_count"})
            lines.append(f"| {row['match_scope']} | {row[label_key]} | {row['event_count']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 CSV, JSON, or JSONL corpus")
    parser.add_argument("--output-dir", type=Path, default=Path("analysis-output"))
    args = parser.parse_args()

    raw_rows = read_rows(args.input)
    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    duplicate_input_ids = 0
    for index, row in enumerate(raw_rows, start=1):
        post_id = str(row.get("post_id") or row.get("id") or "").strip()
        canonical_url = str(row.get("canonical_url") or row.get("url") or "").strip()
        stable_id = post_id or canonical_url
        if stable_id and stable_id in seen_ids:
            duplicate_input_ids += 1
            continue
        if stable_id:
            seen_ids.add(stable_id)
        row = dict(row)
        row.setdefault("post_id", post_id or f"row-{index}")
        row.setdefault("canonical_url", canonical_url)
        deduped.append(row)

    annotated = [annotate(row) for row in deduped]
    matched = [row for row in annotated if row["match_scope"] != "none"]
    excluded = [row for row in annotated if row["match_scope"] == "none"]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(args.output_dir / "normalized_posts.csv", matched)
    write_csv(args.output_dir / "excluded_posts.csv", excluded)
    write_csv(args.output_dir / "monthly_frequency.csv", frequency_rows(matched))
    write_csv(args.output_dir / "co_mentions.csv", co_mentions(matched))

    dimensions = {}
    for field, filename, title in [
        ("topics", "topic_frequency.csv", "Topics"),
        ("industries", "industry_frequency.csv", "Industries"),
        ("policy_instruments", "policy_frequency.csv", "Policy instruments"),
        ("korea_context", "korea_context_frequency.csv", "Korea context"),
        ("stance", "stance_frequency.csv", "Stance"),
    ]:
        rows = dimension_rows(matched, field)
        write_csv(args.output_dir / filename, rows)
        dimensions[title] = rows

    summary = make_summary(matched, duplicate_input_ids, len(excluded))
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(args.output_dir / "report.md", summary, dimensions)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
