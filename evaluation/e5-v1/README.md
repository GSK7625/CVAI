# Đánh giá Colab — E5 + MLP v1

Nguồn: metrics/predictions người dùng xuất sau full. Trọng số chính xác nằm
trong artifact và Release, classifier SHA-256:

```text
268e14e927fcd94d6ffa89f9cc0524691e5d18567d7f995355eb8aa1be0e5105
```

150 cặp CV–JD tổng hợp, 600 yêu cầu, cùng rubric và split trong repository.

| Chỉ số | Cosine baseline | E5 + MLP |
|---|---:|---:|
| Macro-F1 | 0,3916 | **0,7636** |
| Accuracy từng yêu cầu | 42,67% | **82,17%** |
| MAE điểm phù hợp /100 | 19,09 | **13,27** |

Ma trận nhầm lẫn, hàng gold/cột dự đoán:

| Gold | met | partial | not_evidenced |
|---|---:|---:|---:|
| met | 106 | 10 | 40 |
| partial | 0 | 52 | 45 |
| not_evidenced | 0 | 12 | 335 |

Đúng 493/600 yêu cầu nhưng chỉ **70/150 cặp đúng cả bốn nhãn**. 85 yêu cầu có
bằng chứng bị gán not_evidenced; 82 trường hợp trong đó đã tìm thấy evidence
gold ở top-3. Đây là điểm yếu của classifier/cách biểu diễn, không chỉ truy xuất.

- Chấm thấp hơn gold: 68 cặp; cao hơn: 11; điểm tổng đúng: 71.
- Sai số có dấu trung bình: −11,09 điểm; không dùng số này để cộng bù điểm.
- Top-3 chứa evidence gold: 250/253 yêu cầu có evidence, recall 98,81%.
- CPU Colab 2 threads: warm p50 0,164 giây/cặp, p95 0,212 giây/cặp.
- Peak RSS process đánh giá: 1.885,52 MiB; không phải RAM toàn VPS.

## Tệp

- `metrics.json`: chỉ số và baseline nguyên bản.
- `test_predictions.jsonl`: dự đoán/ngữ cảnh từng mẫu, không sửa đáp án máy.
- `model_manifest.json`: cấu hình/revision/hash của model Colab đã tải về.
- `reproduction.json`: kiểm tra trọng số và tái tính kết quả local.

Không có validation_metrics của run Colab trong gói người dùng cung cấp;
không thay bằng kết quả validation từ một run local khác.

Đây là test tổng hợp đã từng được quan sát trong phát triển. Chưa có kiểm
duyệt chuyên gia trên CV thật, chưa đánh giá parser JD thô hoặc VPS thực.
Không suy ra khả năng tuyển dụng hay độ chính xác trên CV/JD tự nhiên.
