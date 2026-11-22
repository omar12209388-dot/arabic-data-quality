# arabic-data-quality

Quality checks for **Arabic and mixed Arabic-English text data**: mojibake detection, script statistics, code-switching flags, digit-system mixing, tatweel padding, diacritic density, dialect-cue scoring and conservative normalization. Dependency-free Python.

Built from Arabic-English evaluation and annotation work, where the same handful of data problems show up in every batch: misdecoded UTF-8, mixed Eastern/Western digits, English fragments hiding in Arabic-expected rows, and "dialect" labels that don't match the text.

**Provenance:** portfolio demonstration. `data/samples.jsonl` is synthetic and written for this demo; no client data. The checks, dialect heuristics and normalization are the reusable part.

## What it does

| Check | Severity | Catches |
|---|---|---|
| `mojibake` | error | UTF-8 Arabic misdecoded as Latin-1 (`Ø§Ù„...` shapes) |
| `mixed_digits` | warning | Eastern Arabic-Indic and Western digits in one string |
| `tatweel` | warning | kashida stretch padding that breaks matching |
| `diacritics` | info | high tashkeel density (fine for liturgical text, noise for NLP labels) |
| `code_switch` | warning | Latin tokens in Arabic-expected rows (skipped when `expected="mixed"`) |
| `punctuation` | info | Latin `?`/`,` inside Arabic runs where `؟`/`،` are conventional |

Plus:

- `guess_dialect(text)` — marker-word heuristic across Egyptian / Levantine / Gulf / MSA, reporting the actual cue hits with a confidence label. A review aid, not a classifier.
- `normalize(text, ...)` — digit folding, tatweel/diacritic stripping, alef unification, whitespace collapse; ya and ta-marbuta unification are opt-in because they destroy valid orthographic distinctions.

## Quick start

```bash
python examples/run_checks.py                      # bundled synthetic samples
python examples/run_checks.py your_data.jsonl      # your own: {"id","expected","text"} per line
python -m unittest discover tests
```

No dependencies beyond Python 3.10+. Exits 1 when any sample has an error-severity finding, so it can gate a data-ingestion step.

## Notes and limits

- The dialect module is deliberately honest: it counts high-precision cue words and shows its evidence. Borderline text gets a `low` confidence and belongs with a human reviewer.
- Normalization defaults are conservative; destructive steps (`ya=True`, `ta_marbuta=True`) are explicit opt-ins.
- The mojibake check detects the failure but does not auto-repair; repair belongs upstream at the decode step.
- The bundled samples are synthetic and seeded so the findings are reproducible; they demonstrate the checks, they are not a quality study of any real dataset.

## Provenance

Portfolio demonstration project, built by Omar Saad with AI assistance. No client or employer data.

## License

MIT — see [LICENSE](LICENSE).
