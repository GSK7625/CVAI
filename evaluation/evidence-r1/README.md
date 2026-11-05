# Tối ưu CVAI — evidence-r1

Ngày báo cáo: 05/11/2026. Đã train, đánh giá và kiểm tra inference CPU.

**Chọn `structured-mlp32`: StandardScaler → MLP 61 → 32 ReLU → 3 nhãn.**
Trọng số mới nằm trong `runs/evidence-r1/selected_artifact/`. V1 vẫn được giữ nguyên.
Đây là bản thử nghiệm có kiểm soát trên dữ liệu tổng hợp, chưa thay model production.

## 1. Kết quả chính

Macro-F1 đo **từng yêu cầu JD**, với ba lớp `met / partial / not_evidenced`.
MAE đo sai số điểm CV–JD trên thang 100. Weight không phải đầu vào MLP.

| Tập | Số cặp / yêu cầu tính được | V1 F1 | Bản augmentation-r1 F1 | Bản chọn F1 | MAE V1 → bản chọn |
|---|---:|---:|---:|---:|---:|
| Validation cũ | 100 / 400 | 0,5773 | 0,7435 | **1,0000** | 18,05 → 0 |
| Validation mới | 48 / 187 | 0,3737 | 0,7777 | **1,0000** | 41,09 → 0 |
| Test cũ, đã được xem khi phát triển | 150 / 600 | 0,7636 | 0,7472 | **1,0000** | 13,27 → 0 |
| Holdout mở sau khi khóa model | 48 / 187 | 0,3451 | 0,7428 | **1,0000** | 44,22 → 0 |

**Không hiểu bảng này là “CV thật chính xác 100%”.** Baseline luật cũng đạt
F1=1 trên test cũ và hai tập validation. Dữ liệu chủ yếu được sinh từ template;
đợt này chứng minh hệ thống thực hiện rubric tốt hơn trên phân phối đó.

Holdout có 192 yêu cầu ban đầu; 5 nhãn `needs_review` bị loại khỏi phép đo ba lớp
theo quy tắc đã định trước. 187 yêu cầu còn lại chưa được người đánh nhãn kiểm tra.
MAE ở những cặp có nhãn bị loại chỉ tính trên các yêu cầu còn lại.

**Độ phủ khi chạy thực tế trên holdout:** 36/48 CV có thể trả điểm tổng;
12/48 CV trả `needs_review`, `score=null`. Bao gồm 5 CV có nhãn mơ hồ và 7 CV
có ngữ cảnh kỹ năng mà parser chưa xử lý chắc chắn. MLP dự đoán đúng nhãn của
7 yêu cầu này trong benchmark, nhưng API vẫn yêu cầu người kiểm tra.
Như vậy F1=1 là chỉ số dự đoán thô trên nhãn hợp lệ, không phải tỷ lệ xử lý tự động 100%.

## 2. Cái gì đã thay đổi?

File `evidence_features.py` trích từ **text yêu cầu và text CV**:

- 5 loại yêu cầu: cơ bản, dự án, công việc, thời gian, chưa nhận diện.
- 8 tín hiệu bằng chứng: công việc, dự án, học tập, liệt kê, phủ định,
  không nhắc đến, chưa rõ bối cảnh, mâu thuẫn.
- 40 tương tác giữa loại yêu cầu và tín hiệu bằng chứng.
- 8 tín hiệu thời gian: số tháng, ngưỡng yêu cầu, tỷ lệ, đủ/chưa có thời gian,
  nhận diện được, dùng khoảng ngày, và khoảng ngày mơ hồ.

Tổng **61 chiều**, không đưa nhãn, evidence gold, weight, ID, nhóm CV/JD hay provenance vào model.
Khớp kỹ năng có ranh giới và ưu tiên tên dài: Java khác JavaScript;
React khác React Native; SQL khác PostgreSQL theo rubric hiện tại.
Khoảng thời gian chỉ được hợp nhất khi ghi rõ tháng và `end exclusive`;
không cộng đôi hợp đồng trùng nhau, không cộng các tổng tháng có thể trùng nhau.

**E5 được giữ để truy xuất ngữ cảnh hiển thị. Embedding E5 không đi vào MLP của
cấu hình thắng.** Đây là kết quả ablation, không phải đã fine-tune encoder E5.
Cấu hình dùng thêm ba cosine E5 cũng đạt cùng F1 validation; quy tắc hòa điểm
đã định trước chọn ít đặc trưng hơn. Chưa có bằng chứng E5 cải thiện phân loại
trên bộ này. MLP chỉ có **2.083 tham số**, file trọng số **10.434 byte**.

Không dùng luật để ghi đè nhãn MLP. Luật là baseline riêng; parser có quyền
chặn điểm tổng khi đầu vào không rõ. Điểm vẫn là
`100 × Σ(weight × value) / Σweight`, với `met=1`, `partial=0.5`, `not_evidenced=0`.

## 3. Thử nghiệm và dữ liệu

Train: **844 cặp / 3.362 yêu cầu**, 312 nhóm CV, 78 nhóm JD.
Validation: **148 cặp / 587 yêu cầu**; giữ hai phần cũ/mới để đánh giá riêng.
Không thay các split hoặc trọng số V1. Không train trên holdout.

Sinh thêm **160 nhóm đối chứng / 480 yêu cầu** chỉ từ CV trong train:
cùng CV/kỹ năng, đổi yêu cầu cơ bản ↔ dự án ↔ công việc.
Đây là nhãn luật chưa được người kiểm tra và **không phải 160 CV độc lập mới**.
Chỉ các candidate có hậu tố `minimal` dùng phần này; model thắng không cần nó.

| Candidate | Chiều | F1 val cũ | F1 val mới |
|---|---:|---:|---:|
| structured-mlp32 — chọn | 61 | 1,0000 | 1,0000 |
| compact-mlp32 — thêm 3 cosine E5 | 64 | 1,0000 | 1,0000 |
| full-mlp64-a0.1 — embedding + signals | 1.984 | 0,8804 | 0,9778 |
| full-mlp64-a1 | 1.984 | 0,9384 | 1,0000 |
| compact-mlp32-minimal | 64 | 1,0000 | 1,0000 |
| full-mlp64-minimal | 1.984 | 0,8623 | 0,9504 |

Scaler fit train; MLP dùng trọng số cân bằng lớp, alpha=0.1, seed=42,
tối đa 500 vòng, dừng sau 70 vòng do hội tụ, không có cảnh báo hội tụ.
Hai seed kiểm tra 43 và 44 đều giữ F1=1 trên hai validation, không chọn lại seed.

Chọn model theo trung bình F1 hai validation. Mỗi validation phải không kém
model tốt nhất trong V1/augmentation-r1 quá 0,005 F1; accuracy của từng loại
yêu cầu không giảm quá 0,01. Chốt model trước khi mở holdout.

## 4. Đối chiếu thống kê và lỗi trọng yếu

Test cũ, `professional/paid_skill`: accuracy **71,91% → 100%**;
bản augmentation-r1 trước đó là 53,93%.
Confusion matrix bản chọn, hàng nhãn thật/cột dự đoán, thứ tự met/partial/not_evidenced:

```text
Test cũ:                 Holdout hợp lệ:
156   0   0               87   0   0
  0  97   0                0  50   0
  0   0 347                0   0  50
```

Bootstrap ghép cặp 5.000 lần, giữ hai model trong cùng đơn vị resample:

- Test cũ, gom chéo JD × CV: ΔF1 so V1 = +0,2364; CI95% [+0,1757; +0,3066].
- Holdout, gom theo JD (mỗi CV chỉ thuộc một JD): ΔF1 so V1 = +0,6549;
  CI95% [+0,6051; +0,7119].
- Holdout so augmentation-r1: ΔF1 = +0,2572; CI95% [+0,1932; +0,3311].

Chỉ có 12 JD holdout, cùng generator/ontology với train. Khoảng tin cậy phản ánh
biến động trong bộ tổng hợp này; không phải độ tin cậy trên CV thật.
Baseline luật trên holdout có coverage 96,26% trong 187 yêu cầu hợp lệ;
F1=0,9749 khi dùng V1 cho phần luật bỏ qua. Không so con số này như luật có coverage 100%.

## 5. Kiểm tra chạy thực tế và hạn chế

- Nạp lại NPZ an toàn, không dùng pickle; dự đoán xuất/nạp khớp trên validation.
- Tái tính độc lập bằng sklearn; kết quả V1 và augmentation-r1 trên test cũ
  khớp chính xác các kết quả đã lưu trước đó.
- Kiểm tra nhóm CV/JD, nội dung và checksum; dataset cũ không đổi.
- Demo JD nguyên văn → parser → yêu cầu/weight → model → nhận xét trả **87,5/100**.
- CPU cục bộ, 2 threads, một CV demo ngắn: warm p50 **0,080 giây**,
  p95 **0,089 giây** trong 5 lượt warm; RSS tiến trình khoảng **708 MiB**.
  Đây không phải benchmark tải đồng thời, CV dài, hoặc đo trên VPS của bạn.

Metric chính dùng yêu cầu JD đã chuẩn hóa. Parser JD nguyên văn vẫn có phạm vi
ngữ pháp/vocabulary giới hạn. Chưa đánh giá PDF/Word/OCR, CV tiếng Việt tự do,
hay CV thật đa dạng. Chưa đổi backend/web đang chạy hoặc phát hành GitHub.

Một lỗi ở bước tạo báo cáo truyền cả `jd_text` và `requirements` đã được sửa.
Hai file dự đoán đã hoàn tất trước lỗi; báo cáo được phục hồi từ CSV đã khóa,
không train lại, không chọn lại model, không chạy lại dự đoán holdout được chấm.
Chi tiết trong `report_recovery.json` và `executed_sources/`.
Sau đó chuyển chặn điểm mơ hồ về renderer chung cho CLI/API/evaluator và sửa
stdout UTF-8 trên Windows; không đổi feature parser, dữ liệu hay trọng số.

Holdout 48 CV đã được sử dụng và được ghi nhận trong
`datasets/human_review_round1/holdout_first_evaluation.json`.
Không dùng lại nó như test mới ở vòng phát triển tiếp theo.

## 6. Chạy thử ngay

Không cần train lại trên Colab. Từ thư mục gốc FutureCV, với môi trường Python đã cài dependencies:

```powershell
python -X utf8 training/lightweight_cv/predict.py --artifact-dir training/lightweight_cv/runs/evidence-r1/selected_artifact --input training/lightweight_cv/example_raw_input.json --output my_cv_review.json
```

Để dùng CV khác, copy `example_raw_input.json`, sửa `cv_text`, `jd_text` và
`job_title`. Không truyền thêm `requirements` cùng `jd_text`.
Nếu `status=needs_review`, kiểm tra `review_required` và `evidence_signals`;
không coi `score=null` là 0 điểm.

Gói `cvai-evidence-r1-cpu.zip` chứa code inference và toàn bộ encoder/classifier.
Sau giải nén, chạy `predict.py --artifact-dir artifact --input example_raw_input.json`.
Thư viện runtime theo `requirements.txt`; cài PyTorch CPU riêng trước khi dùng.
API dùng `server.py` như bản cũ, trỏ `CVAI_ARTIFACT_DIR` đến artifact mới;
giữ một worker và khóa API nội bộ. Tự động hóa đánh giá ứng viên vẫn cần người đối chiếu.

Tái lập phần train/validation ở thư mục output mới:

```powershell
python -X utf8 training/lightweight_cv/optimize_evidence.py --output training/lightweight_cv/runs/evidence-reproduce --threads 2
```

Không mở lại holdout bằng run mới. Dùng các CSV trong báo cáo để tái tính chỉ số.
Mọi candidate/seed, hash, dự đoán và quyết định được giữ trong `runs/evidence-r1/`.

Tham khảo chính thức: [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small)
và [MLPClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html).
Bước tiếp theo có giá trị là gold từ CV có quyền sử dụng, do người kiểm tra độc lập;
không tiếp tục thêm template để làm các số 1,00 đẹp hơn.
