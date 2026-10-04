# Data Profile — Phase 01

Generated: 2026-10-04T05:23:01.472671+00:00
Taxonomy version: `v0.1`
Raw archive SHA-256: `635241ed09ccee18bdae1f83b45f26d6759e0aa2513c529f6190e9054062436c`

> This profile distinguishes the real 2023 archive sample from the saved fresh snapshot. Synthetic fixtures are excluded. Coverage/count metrics are not extraction accuracy.

## Sample summary

| Measure | Historical archive sample | Saved fresh snapshot |
|---|---:|---:|
| Rows | 300 | 267 |
| Date range | 2023-01-02 23:42:31 to 2023-12-31 20:02:52 | 2026-08-19 12:12:11 to 2026-09-19 11:40:08 |
| Observed months | 12 | 2 |
| Rows with source skill tags | 219 | 14 |
| Rows with original description | 0 | 267 |
| Mean description length (available rows only) | N/A — archive has no JD | 8203.4 |
| Candidate duplicate pairs (same title + company heuristic) | 0 | 14 |

## Historical sample by month

| Month | Rows |
|---|---:|
| 2023-01 | 25 |
| 2023-02 | 25 |
| 2023-03 | 25 |
| 2023-04 | 25 |
| 2023-05 | 25 |
| 2023-06 | 25 |
| 2023-07 | 25 |
| 2023-08 | 25 |
| 2023-09 | 25 |
| 2023-10 | 25 |
| 2023-11 | 25 |
| 2023-12 | 25 |

## Fresh snapshot by source and month

Sources: arbeitnow: 250, remotive: 17

| Month | Rows |
|---|---:|
| 2026-08 | 6 |
| 2026-09 | 261 |

## Interpretation and limitations

- The historical sample is drawn from the checked-in archive and covers 2023 only. The archive has `job_skills` source tags but no `job_description`; these records cannot evaluate extraction from JD text.
- The fresh data is a saved snapshot, not evidence of current API availability or a continuous time series.
- Title/company duplicates are candidates for review, not exact deduplication counts.
- Source-tag presence and rule-based skill coverage measure availability/coverage only. Precision, recall and accuracy require independent labels.
- A missing month means no observation in that sample/source; it must not be interpreted as zero market demand.
- Synthetic demo fixtures under `data/fixtures/synthetic/` are excluded from this report and all feasibility decisions.
