# Sơ đồ tiến độ dự án — cập nhật 15/10/2026

Trạng thái dựa trên bằng chứng chạy thật và giới hạn nghiệm thu, không quy đổi thành phần trăm. Nhánh Gold hiện hành dùng archive 2023 và snapshot API 666 dòng; đợt Bronze 2026 mới được trình bày riêng.

```mermaid
flowchart TB
    A["Archive 2023 + API snapshot 666"] --> B["Bronze + manifest đã khóa"]
    B --> C["Spark ETL local → Silver/provenance<br/>786.300 tin, 1:1"]
    C --> D["Gold mô tả · 5 bảng<br/>run 04/10"]
    D --> E["Parquet serving · verified"]
    D --> M["MongoDB serving · 5 bảng<br/>audit/hash verified 15/10"]
    E --> F["JobScope · 6 trang"]
    M --> F
    B --> H["HDFS Bronze → Spark ETL → Silver<br/>666 → 661, đã chạy thật 15/10"]
    H --> H2["M2 còn mở: snapshot nhiều kỳ,<br/>ổn định nguồn, nghiệm thu lab"]

    N["Bronze 2026 mới · 19.706 ID"] --> N2["23 run đã audit<br/>GLOBAL / US_FEDERAL tách biệt"]
    N2 --> V["Trang kiểm kê Bronze 2026"]
    N2 --> L["M4 · mẫu 95 JD local<br/>chờ gán nhãn độc lập"]
    L -. "chưa qua gate chất lượng" .-> C

    D --> G{"Gate dự báo NO_GO<br/>32 tháng thiếu trong Gold run"}
    G --> G1["M6 / model M7 chờ dữ liệu đủ điều kiện"]
    G --> G2["Hồ sơ M7 NO_GO đã soạn<br/>chờ nghiệm thu"]

    F --> Z["M10 · báo cáo, nội dung slide,<br/>kịch bản demo đã soạn"]
    H2 --> Z2["Nghiệm thu nhóm/giảng viên còn mở"]
    G2 --> Z2
    L --> Z2
    Z --> Z2

    classDef done fill:#d8f3dc,stroke:#2d6a4f,color:#183a27;
    classDef pending fill:#fff3cd,stroke:#a66b00,color:#4d3500;
    classDef blocked fill:#f8d7da,stroke:#a02a35,color:#5c1720;
    class A,B,C,D,E,F,H,M,N,N2,V,Z done;
    class H2,L,G2,Z2 pending;
    class G,G1 blocked;
```

M3/M5 có output local được kiểm chứng, M8 có cả Parquet và MongoDB, M9 có giao diện chạy và test. M2/M3/M4/M5/M7/M8/M9/M10 vẫn cần các quyết định nghiệm thu nêu trong [README](../../README.md) và [báo cáo cuối](../final/FINAL_REPORT_2026-10-15.md). Đường HDFS→Silver là run kiểm thử fresh 666 dòng, không thay Gold 786.300 tin. Bản ghi Bronze 2026 không được coi là nhu cầu IT đã xác nhận; forecast giữ `NO_GO`.
