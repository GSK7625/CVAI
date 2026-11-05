# CVAI: model CPU → ASP.NET Core → React

Luồng đã nối: ứng viên chọn CV tại trang ứng tuyển → Phân tích →
POST /api/candidate/jobs/{jobId}/preview-match → kiểm tra quyền sở hữu CV →
CvParser.RawText + Job.Requirements (hoặc Description khi thiếu Requirements) →
dịch vụ CPU /review → evidenceReview → bảng từng yêu cầu, weight và đoạn CV.

Đây là đánh giá thử nghiệm, không tự quyết định tuyển dụng. Score null là cần
kiểm tra, không phải 0 điểm. Điểm legacy trong response cũ được giữ để tương thích;
khi matchSource=evidence, frontend chỉ dùng evidenceReview.score/status.
Luồng apply/ranking và CV quality analysis cũ không bị thay bằng điểm này.

## Chạy dịch vụ model

Tại thư mục gốc repo, tạo Python venv và cài dependencies:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
python -m pip install -r training/lightweight_cv/requirements.txt
python training/lightweight_cv/fetch_evidence_model.py
$env:CVAI_ARTIFACT_DIR = (Resolve-Path models/evidence-r1).Path
$env:INTERNAL_API_KEY = "<chuoi-ngau-nhien-it-nhat-32-ky-tu>"
python -m uvicorn server:app --app-dir training/lightweight_cv --host 127.0.0.1 --port 8001 --workers 1
```

Linux: source .venv/bin/activate và export các biến tương ứng.
Có ZIP đã tải: thêm --zip /path/cvai-evidence-r1-cpu.zip vào lệnh fetch.
Encoder chạy offline sau khi tải. Không cần API OpenAI/Gemini cho evidence review.

## Bật ở ASP.NET Core

Trong terminal chạy backend, cấu hình bằng biến môi trường hoặc user-secrets:

```powershell
$env:EvidenceAi__Enabled = "true"
$env:EvidenceAi__BaseUrl = "http://127.0.0.1:8001"
$env:EvidenceAi__ApiKey = "<cung-khoa-voi-INTERNAL_API_KEY>"
dotnet run --project backend/src/FutureCV.Api
```

Giữ cấu hình DB/auth/storage hiện có. Nếu chạy trong container, thay BaseUrl bằng
hostname nội bộ của dịch vụ AI. Không public cổng model; không đưa khóa vào VITE_*
hoặc frontend. Feature flag mặc định tắt để rollout có kiểm soát; bật flag sẽ ưu
 tiên evidence review hơn hai chế độ AI preview cũ. Tắt flag để rollback V1.

Frontend dùng URL/backend và session hiện có: `cd frontend`, `npm ci`, `npm run dev`.
Đăng nhập ứng viên, tải/phân tích PDF, mở một tin tuyển dụng và chọn CV ở trang
ứng tuyển. Nhấn Phân tích; đổi CV sẽ yêu cầu phân tích lại.

## Phạm vi và trạng thái

- PDF tải lên sẽ được đọc trực tiếp bởi dịch vụ CPU ở lần Phân tích đầu tiên;
  lưu text gốc trong CVParsers để tái sử dụng. CV cũ còn Pending cũng được xử lý.
  Không cần dịch vụ AI cũ cổng 8000 cho luồng evidence. Cập nhật dependencies bằng
  `python -m pip install -r training/lightweight_cv/requirements.txt`, rồi restart model.
  API nội bộ POST /extract-pdf nhận base64, xác thực cùng khóa; giới hạn 5MB,
  50 trang, 30.000 ký tự, worker riêng timeout 15 giây. Không OCR/Word/PDF khóa.
  JSON của CV builder không được giả làm text gốc. PDF chỉ tải từ host Cloudinary
  được cho phép, không theo redirect và không gửi khóa model tới Cloudinary.
  Tệp bị chặn tải công khai được backend tải qua Cloudinary DownloadPrivate với
  chữ ký hết hạn sau 1 phút, sau khi đã kiểm tra quyền sở hữu CV; không cần mở
  public PDF trong cấu hình Cloudinary.
- Requirements là nguồn yêu cầu được chấm, Description là fallback; chưa hợp nhất
  các trường kinh nghiệm/học vấn bổ sung của job vào rubric. Không gọi đây là
  đánh giá đầy đủ mọi điều kiện của tin tuyển dụng.
- Parser JD có phạm vi giới hạn. HTTP 422 từ model trả needs_review thay vì điểm giả.
- Model bận, timeout, thiếu cấu hình: unavailable và nút thử lại; ứng tuyển vẫn hoạt động.
- Không lưu CV mới vào training, không ghi log nội dung CV hoặc khóa API.
- Không cần migration DB. Không tự áp dụng score vào quyết định tuyển dụng.
- Encoder E5 truy xuất ngữ cảnh; MLP được chọn dùng 61 đặc trưng tường minh.
  Xem evaluation/evidence-r1/README.md: dữ liệu tổng hợp, 36/48 CV holdout có điểm tự động.

## Kiểm chứng

Backend có test quyền sở hữu CV, text gốc, score=null và HTTP contract;
frontend typecheck/build và test có sẵn. Test contract cũ đã sửa đường dẫn fixtures
hardcode ổ D để chạy được trên checkout khác.
Chưa chạy phiên đăng nhập E2E trên DB/VPS production. Đừng hiểu code đã push là
VPS đã được triển khai. Bộ kiểm tra .NET trên máy phát triển dùng runtime 10
roll-forward vì máy chưa có ASP.NET runtime 8.

Mã nguồn giữ nguyên V1 và không đưa pair-classifier v2 vào lần phát hành này.
Trọng số lớn ở Release cvai-evidence-r1; NPZ nhỏ và manifest ở Git.

## Sửa lỗi nhầm CV khi phân tích lại

Nút phân tích không truyền React click event làm ID CV. Mỗi yêu cầu phân tích
nhận CV ID tường minh, không refetch query đang giữ ID cũ sau khi đổi/tải CV.
Kết quả được kiểm tra cặp jobId/cvId và yêu cầu cũ không ghi đè yêu cầu mới.
