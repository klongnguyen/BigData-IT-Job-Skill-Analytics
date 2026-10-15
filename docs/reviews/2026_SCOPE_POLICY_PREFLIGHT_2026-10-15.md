# Preflight phạm vi IT 2026

- Gate: **PASSED**
- Nguồn: 23 Bronze run đã pin SHA; mẫu AI review 175 dòng.
- Input: 21,435; valid: 21,435; quarantine: 0; duplicate: 1,729; unique: 19,706.
- Silver dự kiến: 8,370; ngoài IT: 548; chưa xác định: 10,788.

## Source × market × quyết định

| Source | Market | Quyết định | Rows |
|---|---|---|---:|
| arbeitnow | GLOBAL | excluded | 543 |
| arbeitnow | GLOBAL | in_scope | 1,621 |
| arbeitnow | GLOBAL | unresolved | 10,788 |
| remotive | GLOBAL | excluded | 5 |
| remotive | GLOBAL | in_scope | 10 |
| usajobs_historic | US_FEDERAL | in_scope | 6,739 |

## Nghề trong Silver dự kiến

| Source | Market | Nghề | Rows |
|---|---|---|---:|
| arbeitnow | GLOBAL | Backend Developer | 131 |
| arbeitnow | GLOBAL | Data Analyst | 37 |
| arbeitnow | GLOBAL | Data Engineer | 117 |
| arbeitnow | GLOBAL | Data Scientist | 90 |
| arbeitnow | GLOBAL | DevOps Engineer | 212 |
| arbeitnow | GLOBAL | Frontend Developer | 56 |
| arbeitnow | GLOBAL | Machine Learning Engineer | 152 |
| arbeitnow | GLOBAL | Other IT | 136 |
| arbeitnow | GLOBAL | Software Engineer | 690 |
| remotive | GLOBAL | Backend Developer | 1 |
| remotive | GLOBAL | Data Scientist | 1 |
| remotive | GLOBAL | Machine Learning Engineer | 2 |
| remotive | GLOBAL | Other IT | 1 |
| remotive | GLOBAL | Software Engineer | 5 |
| usajobs_historic | US_FEDERAL | Backend Developer | 1 |
| usajobs_historic | US_FEDERAL | Data Analyst | 7 |
| usajobs_historic | US_FEDERAL | Data Engineer | 26 |
| usajobs_historic | US_FEDERAL | Data Scientist | 13 |
| usajobs_historic | US_FEDERAL | DevOps Engineer | 33 |
| usajobs_historic | US_FEDERAL | Frontend Developer | 2 |
| usajobs_historic | US_FEDERAL | Machine Learning Engineer | 4 |
| usajobs_historic | US_FEDERAL | Other IT | 6,603 |
| usajobs_historic | US_FEDERAL | Software Engineer | 50 |

## Tháng quan sát

| Source | Market | Tháng | Rows |
|---|---|---|---:|
| arbeitnow | GLOBAL | 2026-10 | 1,621 |
| remotive | GLOBAL | 2026-09 | 8 |
| remotive | GLOBAL | 2026-10 | 2 |
| usajobs_historic | US_FEDERAL | 2026-01 | 500 |
| usajobs_historic | US_FEDERAL | 2026-02 | 599 |
| usajobs_historic | US_FEDERAL | 2026-03 | 754 |
| usajobs_historic | US_FEDERAL | 2026-04 | 747 |
| usajobs_historic | US_FEDERAL | 2026-05 | 719 |
| usajobs_historic | US_FEDERAL | 2026-06 | 772 |
| usajobs_historic | US_FEDERAL | 2026-07 | 771 |
| usajobs_historic | US_FEDERAL | 2026-08 | 820 |
| usajobs_historic | US_FEDERAL | 2026-09 | 760 |
| usajobs_historic | US_FEDERAL | 2026-10 | 297 |

## Tiêu đề chưa xác định thường gặp

| Source | Title | Rows |
|---|---|---:|
| arbeitnow | Account Executive | 25 |
| arbeitnow | Servicetechniker im Außendienst (gn) | 23 |
| arbeitnow | Forward Deployed Engineer | 18 |
| arbeitnow | Geschäftsführer (m/w/d) Gebäude-Energieberatung – Aufbau neuer Standort im Umland | 16 |
| arbeitnow | Enterprise Account Executive | 16 |
| arbeitnow | IT-Systemadministrator (m/w/d) | 16 |
| arbeitnow | Initiativbewerbung | 13 |
| arbeitnow | Senior Product Designer | 11 |
| arbeitnow | IT-Administrator (m/w/d) | 10 |
| arbeitnow | Senior Sales Engineer - UK | 10 |
| arbeitnow | Engineering Manager | 10 |
| arbeitnow | Initiativbewerbung (m/w/d) | 10 |
| arbeitnow | Senior Product Manager | 9 |
| arbeitnow | Product Manager | 8 |
| arbeitnow | Projektleiter Customer Projects (gn) | 8 |

## Rule được kích hoạt

| Source | Rule ID | Rows |
|---|---|---:|
| arbeitnow | insufficient_title_evidence | 10,788 |
| arbeitnow | it_digital_architecture | 7 |
| arbeitnow | it_mapped_v0_2 | 1,485 |
| arbeitnow | it_pos_support | 3 |
| arbeitnow | it_qa_testing | 5 |
| arbeitnow | it_security | 66 |
| arbeitnow | it_software_implementation | 4 |
| arbeitnow | it_solution_engineering | 10 |
| arbeitnow | it_support_operations | 41 |
| arbeitnow | non_it_commercial_admin | 508 |
| arbeitnow | non_it_domain_profession | 23 |
| arbeitnow | not_a_job_training | 12 |
| remotive | it_mapped_v0_2 | 9 |
| remotive | it_support_operations | 1 |
| remotive | non_it_commercial_admin | 5 |
| usajobs_historic | source_series_2210 | 6,739 |

## Gate và giới hạn

Các nhãn mẫu là AI-assisted, không phải human ground truth; số khớp mẫu không phải precision/recall/F1.
Tháng không quan sát không được zero-fill. GLOBAL và US_FEDERAL có mẫu số riêng.
Forecast gate vẫn NO_GO. Preflight chỉ đọc Bronze, chưa xuất bản Silver.
