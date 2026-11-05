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

## Khởi động lại local với cùng khóa

Lưu EvidenceAi.Enabled=true, BaseUrl=http://127.0.0.1:8001 và ApiKey ngẫu nhiên
ít nhất 32 ký tự trong appsettings.Development.json (file được Git bỏ qua).
Ba terminal tại thư mục repo:

```powershell
# Terminal model: kích hoạt venv đã cài dependencies trước
./scripts/start-local.ps1 model
# Terminal backend
./scripts/start-local.ps1 backend
# Terminal frontend
./scripts/start-local.ps1 frontend
```

Hai dịch vụ đọc cùng khóa từ file local; không in khóa hoặc đưa vào frontend.
Nếu đang chạy các lệnh cũ, dừng bằng Ctrl+C rồi dùng script tương ứng.
Điểm chất lượng CV ở trang quản lý CV là luồng cũ, tách biệt với E5/MLP so khớp
JD. Khi PDF chỉ có text, chưa có dữ liệu cấu trúc được xác minh, luồng quality
sẽ báo chưa đủ dữ liệu thay vì chấm thiếu kỹ năng/học vấn trên hồ sơ trống.

## Xem CV PDF và đọc JD

- Preview CV gọi endpoint có xác thực `/api/candidate/cvs/{id}/preview-url`.
  Backend kiểm tra quyền sở hữu và cấp URL tải PDF inline có hạn 2 phút; không mở
  trực tiếp URL Cloudinary public đang bị ACL chặn.
- `/jobs/prepare`, `/review`, `prepare_jd.py` và `predict.py` dùng `jd_parser_v2.py`.
  Bộ trích đặc trưng `jd_parser.py`/`evidence_features.py` và checksum artifact
  vẫn giữ nguyên; benchmark huấn luyện tiếp tục dùng parser đã đóng băng.
- V2 đọc câu EN/VI, HTML, tiêu đề mục, mức ưu tiên, phủ định, nhóm AND/OR,
  kỹ năng, khoảng thời gian, bằng cấp, ngoại ngữ và chứng chỉ. Gộp yêu cầu lặp,
  giữ nguyên nguồn trong `criteria[].sources`; offsets tham chiếu `source_text`
  (văn bản đã bỏ HTML). Profile có hash phiên bản, được tính lại để chống chỉnh sửa.
- Parser `status=ready` nghĩa là đã tách được điều kiện, chưa có nghĩa model
  hỗ trợ chấm mọi điều kiện. Model chỉ nhận các tiêu chí nguyên tử thuộc phạm vi
  đã huấn luyện. Nhóm OR lấy mức cao nhất; AND lấy mức thấp nhất. Kỹ năng ngoài
  model, chứng chỉ/ngoại ngữ/bằng cấp, mức nâng cao, kinh nghiệm riêng kỹ năng,
  thời gian xấp xỉ/khoảng/tối đa được giữ rõ để đối chiếu, không tự đổi thành tối thiểu.
- `score_scope=recognized_skills_and_experience`: điểm phản ánh kỹ năng/mức kinh
  nghiệm nhận diện được, không xác minh toàn bộ nhiệm vụ nghiệp vụ. Điều kiện JD
  chưa hiểu nằm trong `jd_profile.unresolved`. Bằng chứng chưa rõ hoặc điều kiện
  chưa chấm được có assessment `status=needs_review`; tổng `score=null`.
  Không chấm tổng trên một phần JD và không bỏ các tiêu chí vượt giới hạn 20.
- Với JD Machine Learning hiện tại: 5 tiêu chí (pandas, Spark, SQL chuyên nghiệp;
  scikit-learn thực hành/dự án; khoảng 4 tháng Data/ML), Airflow không bắt buộc.
  CV thiếu bối cảnh hoặc mốc xấp xỉ chưa rõ vẫn cần đối chiếu, không phải lỗi đọc JD.
- HTTP 422 do input sai được phân biệt với 422 chứa `jd_profile` từ server cũ.
  `requirements` và profile V1 giữ hợp đồng kiểm tra cũ. V2 không thêm LLM hoặc
  gửi CV ra dịch vụ bên ngoài. Bộ đọc là quy tắc IT EN/VI có giới hạn; câu chưa
  nhận diện được được giữ lại để xem, không coi đây là NLP cho mọi JD.

### Mốc kinh nghiệm xấp xỉ

`review_policy_version=jd-evidence-v2.1`: với JD "khoảng N tháng", bằng chứng
thời gian rõ ràng, đúng vai trò, được trả lương và đúng N tháng được đánh giá đáp
ứng bằng quy tắc `exact_duration_evidence`; giữ đoạn CV nguyên văn để đối chiếu.
Không tự đặt biên dung sai. Tổng thời gian khác N, xấp xỉ, mâu thuẫn hoặc thiếu
bằng chứng vẫn cần kiểm tra. Các kết quả kỹ năng tiếp tục do model đánh giá.
