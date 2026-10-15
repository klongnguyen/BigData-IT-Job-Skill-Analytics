# Sơ đồ tiến độ dự án — 15/10/2026

Sơ đồ này ghi **trạng thái theo bằng chứng**, không quy đổi thành phần trăm hoàn thành. Silver/Gold và dashboard là run local đã khóa ngày 04/10; HDFS là smoke live ngày 15/10. Đợt dữ liệu 2026 mới đã vào Bronze/audit ngày 15/10 nhưng chưa vào Silver/Gold.

```mermaid
flowchart TB
    A["Input run đã khóa<br/>Archive 2023: 785.741 dòng<br/>API 2026: 666 dòng, partial"] --> B["M2 · Bronze + manifest<br/>local: đã có"]
    B --> C["M3 · Spark Silver + provenance<br/>786.300 tin · đã kiểm chứng local"]
    C --> D["M5 · Gold mô tả<br/>5 bảng · đã kiểm chứng local"]
    D --> E["M8 · Parquet serving<br/>đã chạy local"]
    E --> F["M9 · JobScope<br/>5 trang · đã chạy local"]

    N["API 2026 mới<br/>19.706 ID nguồn raw"] --> N2["23 Bronze run được audit<br/>GLOBAL và US_FEDERAL tách biệt"]
    N2 --> N3["M4 · lọc phạm vi IT / đánh giá taxonomy<br/>91,7% title chưa khớp 8 nghề"]
    N3 -. "chờ chất lượng và nghiệm thu" .-> C

    B -.-> H["HDFS → Spark → Parquet<br/>cổng kỹ thuật đạt 15/10"]
    H -.-> H2["M2 còn mở: HDFS → ETL → Silver,<br/>thu fresh định kỳ, replica, nghiệm thu"]
    C -.-> C2["M3 còn nghiệm thu dataset"]
    C -.-> T["M4 còn đánh giá taxonomy<br/>trên nhãn độc lập"]
    D -.-> D2["M5 còn nghiệm thu phân tích"]
    E -.-> E2["M8 còn MongoDB nếu yêu cầu<br/>và nghiệm thu tích hợp"]
    F -.-> F2["M9 còn demo và nghiệm thu tích hợp"]

    D --> G{"Cổng dự báo của Gold đã khóa<br/>NO_GO · thiếu 32 tháng"}
    G --> G1["M6 · ML Dataset<br/>chưa triển khai, bị chặn"]
    G --> G2["M7 · mô hình dự báo<br/>chưa triển khai, bị chặn"]
    G --> G3["M7 · hồ sơ NO-GO<br/>đã soạn, chờ chấp thuận"]

    F2 --> Z["M10 · báo cáo cuối và bàn giao<br/>chưa hoàn tất"]
    G3 --> Z

    classDef verified fill:#d8f3dc,stroke:#2d6a4f,color:#183a27;
    classDef pending fill:#fff3cd,stroke:#a66b00,color:#4d3500;
    classDef blocked fill:#f8d7da,stroke:#a02a35,color:#5c1720;
    class A,B,C,D,E,F,H,N,N2 verified;
    class H2,C2,T,D2,E2,F2,G3,Z,N3 pending;
    class G,G1,G2 blocked;
```

**Chú giải:** xanh = có bằng chứng triển khai local/kỹ thuật; vàng = còn việc hoặc nghiệm thu; đỏ = cổng dự báo `NO_GO`, nhánh model bị chặn. M2 HDFS technical gate đạt **không** đồng nghĩa M2 được nghiệm thu. 19.706 bản ghi Bronze mới **không phải** 19.706 tin IT đã xác nhận; dashboard vẫn đọc Gold cũ và chưa công bố dự báo.

**Nguồn đối chiếu:** [báo cáo tiến độ](../../README.md), [audit Bronze 2026](../data/2026_ingestion_audit.json), [báo cáo dữ liệu 2026](../reviews/2026_DATA_EXPANSION_2026-10-15.md), [review M2 HDFS](../reviews/M2_HDFS_REVIEW_2026-10-15.md), [báo cáo Phase 03](../reviews/PHASE_03_ANALYTICS_REPORT.md), [hồ sơ M7 NO-GO](../reviews/M7_NO_GO_ACCEPTANCE.md), [Final Plan](../../FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md).
