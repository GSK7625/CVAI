# CVAI Controlled Synthetic Dataset v1

950 cặp CV–JD, input tiếng Anh, target nhận xét tiếng Việt. Dữ liệu sinh theo
quy tắc có kiểm soát, không phải CV thật hay nhãn chuyên gia. Không dùng điểm
matched_score của CSV nguồn làm ground truth.

| Split | Cặp | CV độc lập | JD độc lập | Nhãn yêu cầu |
|---|---:|---:|---:|---:|
| train | 700 | 168 | 42 | 2.800 |
| validation | 100 | 36 | 12 | 400 |
| test | 150 | 36 | 12 | 600 |

Sáu nhóm nghề: backend, frontend, QA, DevOps, data/ML, mobile. Các trạng thái
nguồn: công việc, dự án, khóa học, chỉ liệt kê, phủ định, không đề cập. CV/JD
groups và nội dung không trùng giữa các split.

## Nhãn và điểm

Mỗi dòng có sample_id, cv_group, jd_group, cv_text, requirements và target.
Target gồm met/partial/not_evidenced cho từng requirement ID. Evidence dương
trích nguyên văn CV; not_evidenced dùng null. [Rubric](LABELING_GUIDE.md).

score = 100 × Σ(weight × status_value) / Σ(weight), với met=1, partial=0,5,
not_evidenced=0.

Trong dữ liệu giả lập: basic weight1, practical weight2, professional weight3,
experience weight2. Đây là quy ước benchmark cố định. Khi parse JD thô, module
dùng [policy ưu tiên](../../lightweight_cv/END_TO_END.md) riêng; không thay
weight benchmark rồi tiếp tục báo cùng kết quả test.

## Tệp và tái lập

- train/validation/test.jsonl: train và đánh giá.
- provenance/candidates.jsonl, jobs.jsonl: kiểm tra nguồn nhãn; không đưa vào đặc trưng.
- metadata.jsonl: thông tin split/track, không phải input model.
- manifest.json: seed20261022 và SHA-256 các tệp phát hành.
- sample_schema.json: schema sample/target gốc.

Sinh lại vào thư mục mới từ root: `python training/build_dataset.py --output /path/to/new_dataset`.
Không random split lại sau khi tách từng requirement thành dòng phân loại.

## Giới hạn

Các split chia sẻ generator/ontology/rubric và nhiều cấu trúc lặp lại. Test đã
được xem trong phát triển. Chưa đánh giá CV dài/PDF/OCR, timeline phức tạp,
CV tiếng Việt hoặc JD thực. Quy ước basic chấp nhận tự liệt kê/khóa học cần
chuyên gia xem lại. Trước vận hành cần dữ liệu thật có quyền sử dụng, gán nhãn
độc lập và test mới theo nhóm CV/JD. Không gộp synthetic và real test gây hiểu nhầm.
