#!/usr/bin/env python3
"""Run the Arabic data-quality checks over the bundled samples.

Usage:
    python examples/run_checks.py [path/to/samples.jsonl]

Writes examples/output/quality_report.json and prints a per-sample
summary with findings and dialect-cue evidence.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arabic_qa.checks import run_checks, script_stats
from arabic_qa.dialect import guess_dialect
from arabic_qa.normalize import normalize


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "samples.jsonl"
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    results = []
    n_errors = n_warnings = 0
    for row in rows:
        text = row["text"]
        expected = row.get("expected", "ar")
        findings = run_checks(text, expected=expected)
        dialect = guess_dialect(text)
        stats = script_stats(text)
        n_errors += sum(1 for f in findings if f.severity == "error")
        n_warnings += sum(1 for f in findings if f.severity == "warning")
        results.append({
            "id": row["id"],
            "expected": expected,
            "script": stats,
            "dialect_guess": {
                "variety": dialect.variety,
                "confidence": dialect.confidence,
                "hits": {k: v for k, v in dialect.hits.items() if v},
            },
            "findings": [
                {"check": f.check, "severity": f.severity, "message": f.message}
                for f in findings
            ],
            "normalized": normalize(text),
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(path.name),
        "samples": len(results),
        "errors": n_errors,
        "warnings": n_warnings,
        "results": results,
    }
    out = ROOT / "examples" / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for r in results:
        flags = " | ".join(
            f"{f['severity']}:{f['check']}" for f in r["findings"]
        ) or "clean"
        d = r["dialect_guess"]
        print(f"{r['id']:10s} ar_ratio={r['script']['arabic_ratio']:.2f} "
              f"dialect={d['variety']}({d['confidence']})  {flags}")
    print(f"\n{len(results)} samples, {n_errors} errors, {n_warnings} warnings")
    print(f"report written to {out / 'quality_report.json'}")
    return 1 if n_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
