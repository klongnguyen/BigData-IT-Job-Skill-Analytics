"""Apply a documented AI-assisted title review to the pinned 2026 sample.

This one-time script refuses a changed or already-labelled input. Its decisions
are a scope review, not independent human labels or accuracy measurements.
"""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "docs/data/2026_it_scope_sample.csv"
MANIFEST = ROOT / "docs/data/2026_it_scope_sample.manifest.json"
ORIGINAL_SHA256 = "34be349a016de434f3bcc3c29bacc5601226004d68e63479cbf3795165d0d54a"
REASON_MAPPED = "AI-assisted: tiêu đề khớp rõ taxonomy hiện hành"
REASON_FEDERAL = (
    "AI-assisted: USAJOBS PositionSeries=2210 xác lập phạm vi IT; "
    "title chưa map vào 8 nhóm"
)

# Row numbers refer only to the immutable, SHA-pinned deterministic sample.
# Every Other IT row from Arbeitnow/Remotive receives an explicit title review.
OTHER_DECISIONS = {
    0: ("ngoài IT", "0", "assay-Entwicklung Pharma là kỹ thuật dược, không phải CNTT"),
    1: ("ngoài IT", "0", "Affiliate Marketing/Creator Manager là marketing"),
    2: ("chưa đủ thông tin", "", "Product Manager không nêu sản phẩm phần mềm hay CNTT"),
    3: ("ngoài IT", "0", "Monteur Tor- und Türsysteme lắp cửa, không phải CNTT"),
    4: ("IT ngoài 8 nhóm", "1", "Support hệ thống POS Kassensysteme là hỗ trợ hệ thống số"),
    5: ("ngoài IT", "0", "Starkstromelektriker là thợ điện công suất lớn"),
    6: ("ngoài IT", "0", "Brandschutztechniker là kỹ thuật phòng cháy"),
    7: ("IT ngoài 8 nhóm", "1", "AI Solutions Engineer là tích hợp giải pháp AI; chưa rõ nghề ML Engineer"),
    8: ("ngoài IT", "0", "Regional Enterprise Sales Manager là bán hàng"),
    9: ("ngoài IT", "0", "Quantitative Risk Manager là quản trị rủi ro tài chính"),
    10: ("ngoài IT", "0", "Teilprojektleiter Offshore Automatisierung/Telekommunikation là dự án công nghiệp"),
    11: ("ngoài IT", "0", "Corporate Sales là bán hàng"),
    12: ("IT ngoài 8 nhóm", "1", "Project Manager triển khai phần mềm là quản lý dự án CNTT"),
    13: ("chưa đủ thông tin", "", "Initiativbewerbung là hồ sơ ứng tuyển mở, không có nghề"),
    14: ("chưa đủ thông tin", "", "Project Manager Real World Data không nêu nhiệm vụ CNTT"),
    15: ("IT ngoài 8 nhóm", "1", "Solution Architect Digital Platforms là kiến trúc giải pháp số"),
    16: ("Software Engineer", "1", "Full-Stack Entwickler là lập trình viên full stack"),
    17: ("ngoài IT", "0", "Influencer Manager là marketing"),
    18: ("ngoài IT", "0", "Director of Ops/Managing Director là quản trị vận hành"),
    19: ("chưa đủ thông tin", "", "Technical Support Specialist không nêu hệ thống được hỗ trợ"),
    20: ("IT ngoài 8 nhóm", "1", "Werkstudent IT Support là hỗ trợ CNTT"),
    21: ("Software Engineer", "1", "Softwareentwickler KI-Anwendungen là phát triển ứng dụng phần mềm"),
    22: ("IT ngoài 8 nhóm", "1", "Solutions Engineer EDI/e-invoicing là tích hợp hệ thống số"),
    23: ("ngoài IT", "0", "HR & People Experience Internship là nhân sự"),
    24: ("ngoài IT", "0", "Appointment/Chat Setter là đặt lịch và bán hàng"),
    25: ("chưa đủ thông tin", "", "Delivery Management Professional Services không nêu dịch vụ CNTT"),
    26: ("ngoài IT", "0", "Game Art Lead là thiết kế mỹ thuật trò chơi"),
    27: ("ngoài IT", "0", "Facharzt Sportmedizin là bác sĩ"),
    28: ("ngoài IT", "0", "Product Manager Soft Fabrics là sản phẩm vải"),
    29: ("ngoài IT", "0", "Bilanzbuchhalter/Accountant là kế toán"),
    30: ("ngoài IT", "0", "Ingenieur Heating & Cooling là kỹ thuật cơ điện"),
    31: ("chưa đủ thông tin", "", "AI Data Specialist - French chưa rõ là kỹ thuật hay gán nhãn ngôn ngữ"),
    32: ("ngoài IT", "0", "Fachkosmetiker là nghề thẩm mỹ"),
    33: ("IT ngoài 8 nhóm", "1", "Teststrategie, QA & IT Consulting là kiểm thử và tư vấn CNTT"),
    34: ("Frontend Developer", "1", "Front-end Developer là lập trình giao diện"),
    35: ("ngoài IT", "0", "Business Development Representative là kinh doanh"),
    36: ("ngoài IT", "0", "Credit Hire Handler là xử lý hồ sơ tín dụng"),
    37: ("IT ngoài 8 nhóm", "1", "Offensive Security/Red Team/AppSec là an ninh mạng"),
    38: ("IT ngoài 8 nhóm", "1", "IT Operations & Cybersecurity là vận hành và bảo mật CNTT"),
    39: ("Machine Learning Engineer", "1", "RF Machine Learning Engineer nêu rõ kỹ thuật ML"),
    80: ("ngoài IT", "0", "Content Reviewer là kiểm duyệt nội dung, không nêu CNTT"),
    81: ("Software Engineer", "1", "Full-Stack Rails Engineer là phát triển phần mềm"),
    82: ("ngoài IT", "0", "Copywriter là viết nội dung"),
    83: ("ngoài IT", "0", "Office Assistant là hành chính"),
    84: ("Software Engineer", "1", "Shopify Developer là phát triển phần mềm thương mại điện tử"),
    85: ("ngoài IT", "0", "Writer là viết nội dung"),
    86: ("ngoài IT", "0", "Inside Sales Contractor là bán hàng"),
    87: ("IT ngoài 8 nhóm", "1", "Tier III Service Desk Engineer là hỗ trợ CNTT"),
}

MAPPED_CORRECTIONS = {
    40: ("IT ngoài 8 nhóm", "1", "IT Systems Engineer không đồng nghĩa DevOps Engineer"),
    48: ("ngoài IT", "0", "Weiterbildung Data Science là khóa đào tạo, không phải vị trí tuyển dụng"),
    63: ("IT ngoài 8 nhóm", "1", "Information Security Infrastructure là nghề bảo mật, không nêu DevOps"),
    76: ("Machine Learning Engineer", "1", "Reinforcement Learning Infrastructure là kỹ thuật ML, không phải Data Scientist"),
    138: ("IT ngoài 8 nhóm", "1", "Infrastructure Engineer không nêu DevOps"),
    139: ("IT ngoài 8 nhóm", "1", "Network Systems Engineer là mạng/hệ thống, không nêu DevOps"),
    148: ("IT ngoài 8 nhóm", "1", "Systems Engineer không nêu DevOps"),
    155: ("IT ngoài 8 nhóm", "1", "Systems Engineer không nêu DevOps"),
    161: ("IT ngoài 8 nhóm", "1", "Network Systems Engineer là mạng/hệ thống, không nêu DevOps"),
    164: ("IT ngoài 8 nhóm", "1", "Systems Engineer không nêu DevOps"),
    167: ("IT ngoài 8 nhóm", "1", "Systems Engineer không nêu DevOps"),
}


def main():
    actual = hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
    if actual != ORIGINAL_SHA256:
        raise ValueError("Refusing to relabel a changed or already-labelled sample")
    with SAMPLE.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if len(rows) != 175 or fieldnames is None:
        raise ValueError("The pinned sample must have exactly 175 rows")
    if any(row["manual_label"] or row["in_scope_it"] or row["review_reason"] for row in rows):
        raise ValueError("Refusing to overwrite existing review labels")
    other_indices = {
        i for i, row in enumerate(rows)
        if row["taxonomy_label"] == "Other IT" and row["source"] in ("arbeitnow", "remotive")
    }
    if set(OTHER_DECISIONS) != other_indices:
        raise ValueError("Explicit decisions do not cover exactly the global Other IT sample")
    if any(rows[i]["taxonomy_label"] == "Other IT" for i in MAPPED_CORRECTIONS):
        raise ValueError("A mapped correction points to an Other IT row")

    for i, row in enumerate(rows):
        taxonomy = row["taxonomy_label"]
        if i in OTHER_DECISIONS:
            label, scope, reason = OTHER_DECISIONS[i]
            row.update(manual_label=label, in_scope_it=scope, review_reason="AI-assisted: " + reason)
        elif i in MAPPED_CORRECTIONS:
            label, scope, reason = MAPPED_CORRECTIONS[i]
            row.update(manual_label=label, in_scope_it=scope, review_reason="AI-assisted: " + reason)
        elif row["source"] == "usajobs_historic" and taxonomy == "Other IT":
            row.update(manual_label="IT ngoài 8 nhóm", in_scope_it="1", review_reason=REASON_FEDERAL)
        elif taxonomy != "Other IT":
            row.update(manual_label=taxonomy, in_scope_it="1", review_reason=REASON_MAPPED)
        else:
            raise ValueError(f"Uncovered sample row {i}")

    with SAMPLE.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = Counter(row["in_scope_it"] or "unresolved" for row in rows)
    by_source = {}
    for source in sorted({row["source"] for row in rows}):
        source_rows = [row for row in rows if row["source"] == source]
        by_source[source] = {
            "rows": len(source_rows),
            "in_scope_it": sum(row["in_scope_it"] == "1" for row in source_rows),
            "out_of_scope_it": sum(row["in_scope_it"] == "0" for row in source_rows),
            "unresolved": sum(row["in_scope_it"] == "" for row in source_rows),
        }
    mapped = [row for row in rows if row["taxonomy_label"] != "Other IT"]
    other = [row for row in rows if row["taxonomy_label"] == "Other IT"]
    agreement = {
        "mapped_same_label_and_in_scope": sum(
            row["manual_label"] == row["taxonomy_label"] and row["in_scope_it"] == "1"
            for row in mapped
        ),
        "mapped_revised_label_in_scope": sum(
            row["manual_label"] != row["taxonomy_label"] and row["in_scope_it"] == "1"
            for row in mapped
        ),
        "mapped_out_of_scope": sum(row["in_scope_it"] == "0" for row in mapped),
        "other_it_to_in_scope": sum(row["in_scope_it"] == "1" for row in other),
        "other_it_to_out_of_scope": sum(row["in_scope_it"] == "0" for row in other),
        "other_it_unresolved": sum(row["in_scope_it"] == "" for row in other),
    }
    manifest.update(
        status="ai_assisted_review_complete",
        labeling_method="AI-assisted semantic title review",
        reviewer_type="AI",
        original_unlabelled_sample_sha256=ORIGINAL_SHA256,
        sample_sha256=hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
        in_scope_counts={"in_scope_it_1": counts["1"], "in_scope_it_0": counts["0"],
                         "unresolved": counts["unresolved"]},
        by_source=by_source,
        agreement_counts=agreement,
        note=("AI-assisted scope spot-check only; not independent human ground truth. "
              "Agreement counts are not precision, recall or F1."),
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": manifest["sample_sha256"], "counts": dict(counts),
                      "by_source": by_source, "agreement": agreement}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
