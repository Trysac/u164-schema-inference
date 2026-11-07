# Project record\n\n## Objective\n\nInfer a JSON Schema 2020-12 from JSON records or CSV rows: merged types, nullability, required keys, nested objects and arrays, date and date-time formats.\n\n## Scope\n\n- The public API as documented in the README.\n- Inference from JSON collections and CSV row iterables.\n- Type merging (mathematical union) and recursive object merging.\n- Detection of RFC 3339 date/date-time formats.\n\n## Out of scope\n\n- Enums, min/max constraints, regex patterns, or $ref deduplication.\n- Processing XLSX or Parquet files.\n- Schema validation or statistics generation.\n\n## Effort metrics\n\n| Metric | Value |\n|---|---|\n| Tokens (input / output) | pending measurement |\n| Hours (human) | pending measurement |\n| Cost (USD) | pending measurement |

## Factory run u164 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4476 | 10213 | 0 | 0 | 0.0208 |
| fix-1 | gemini-3.8-flash | no | 21717 | 2372 | 0 | 39119 | 0.0281 |
| fix-2 | gemini-3.8-flash | no | 76718 | 2614 | 0 | 530019 | 0.1071 |
| fix-3 | gemini-3.8-flash | no | 13375 | 242 | 0 | 9030 | 0.0116 |
| fix-4 | gemini-3.8-flash | no | 21813 | 343 | 0 | 42567 | 0.0208 |
| audit | gemini-3.1-flash-lite | no | 72514 | 275 | 0 | 150485 | 0.0223 |
| docs | gemini-3.1-flash-lite | no | 182197 | 1260 | 0 | 0 | 0.0474 |

Total: $0.2582. Prices: Anthropic list prices.
