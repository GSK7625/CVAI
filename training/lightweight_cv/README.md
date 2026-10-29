# E5 + MLP v1

E5-small đóng băng → truy xuất top-3 đoạn CV → MLP phân loại ba nhãn →
tính điểm bằng code. Không yêu cầu nhà tuyển dụng nhập weight.

## Chạy Windows CPU

Từ root repository, PowerShell, Python3.10–3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r training/lightweight_cv/requirements.txt
.\.venv\Scripts\python.exe training/lightweight_cv/fetch_model.py
.\.venv\Scripts\python.exe -X utf8 training/lightweight_cv/predict.py --artifact-dir training/lightweight_cv/artifact --input training/lightweight_cv/example_raw_input.json
```

Muốn tải bằng tay: lấy `cvai-e5-v1-model.zip` từ [Release](https://github.com/GSK7625/CVAI/releases/tag/cvai-e5-v1.0.0),
dùng `fetch_model.py --zip /path/to/cvai-e5-v1-model.zip` để kiểm tra và cài.
Trọng số E5/hash/tokenizer lấy nguyên vẹn từ run Colab đã đánh giá.

Input JSON: `cv_text`, `jd_text`, `job_title` nếu có, `sample_id` tùy chọn.
Ví dụ có sẵn trong `example_raw_input.json`. CV cần là text; PDF/OCR là bước
riêng của ứng dụng. Output có score, nhãn, trích đoạn và nhận xét theo mẫu.

## API nội bộ

Chạy từ thư mục `training/lightweight_cv`, đặt biến môi trường:

- `CVAI_ARTIFACT_DIR`: đường dẫn tuyệt đối tới thư mục artifact.
- `INTERNAL_API_KEY`: khóa riêng ít nhất 32 ký tự, chỉ backend biết.
- `CVAI_THREADS=2`: số threads CPU.

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8010 --workers 1 --no-access-log
```

- `GET /health`
- `POST /jobs/prepare`: `{job_title, jd_text}` → profile/weight.
- `POST /review`: CV + JD thô hoặc CV + job_profile đã lưu.
- POST dùng header `X-Internal-API-Key`. Chỉ một request chấm CV đồng thời.

Backend chọn job_profile theo Job ID, lưu phiên bản và gọi API nội bộ.
Frontend không gọi trực tiếp API AI. Website hiện có chưa tích hợp module này.
Xem [luồng JD](END_TO_END.md).

## Train lại trên Colab

1. Mở `train_e5_classifier.ipynb`.
2. Tạo bundle bằng `python training/lightweight_cv/build_bundle.py` từ root.
3. Upload bundle vào `MyDrive/FutureCV-ML/lightweight/futurecv_e5_bundle.zip`.
4. Chạy smoke rồi full theo notebook; output hai chế độ tách riêng.
5. Chọn cấu hình bằng validation trước khi mở test; mục6 thử CV, mục7 xuất model.

Full: StandardScaler fit train, so sánh ba Logistic Regression và hai MLP64,
chọn macro-F1 validation. Encoder không cập nhật. File `classifier.npz` chứa
scaler và hệ số MLP, không dùng executable pickle/joblib.

## Đánh giá và giới hạn

```bash
python training/lightweight_cv/evaluate.py --data-dir training/datasets/cvai_v1 --artifact-dir training/lightweight_cv/artifact --device cpu
python training/lightweight_cv/analyze_results.py --zip /path/to/evaluation.zip --output /path/to/new_analysis.json
```

Script không ghi đè kết quả cũ. [Kết quả chính thức của run Colab](../../evaluation/e5-v1/README.md).
Model còn bỏ sót bằng chứng rõ ràng; chưa kiểm duyệt CV thật, chưa benchmark
VPS. V1 có thể dùng làm demo/thí nghiệm, không phải công cụ quyết định tuyển dụng.
