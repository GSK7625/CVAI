# 🔑 Hướng dẫn lấy API Key và Cấu hình Dịch vụ AI (FutureCV Backend AI)

Tài liệu này hướng dẫn chi tiết từ A đến Z cách đăng ký **Google Gemini API Key** (hoặc **OpenAI API Key**), cấu hình biến môi trường trong file `.env` của `backend-ai`, và đồng bộ hóa kết nối với **ASP.NET Core Backend**.

---

## 📑 Mục lục
1. [Tổng quan hệ thống AI trong FutureCV](#1-tổng-quan-hệ-thống-ai-trong-futurecv)
2. [Hướng dẫn lấy Google Gemini API Key (Miễn phí)](#2-hướng-dẫn-lấy-google-gemini-api-key-miễn-phí)
3. [Hướng dẫn lấy OpenAI API Key (Tùy chọn)](#3-hướng-dẫn-lấy-openai-api-key-tùy-chọn)
4. [Cấu hình biến môi trường (`backend-ai/.env`)](#4-cấu-hình-biến-môi-trường-backend-aienv)
5. [Đồng bộ cấu hình với ASP.NET Core Backend](#5-đồng-bộ-cấu-hình-với-aspnet-core-backend)
6. [Kiểm tra hoạt động sau khi cấu hình](#6-kiểm-tra-hoạt-động-sau-khi-cấu-hình)
7. [Các lỗi thường gặp và cách xử lý (Troubleshooting)](#7-các-lỗi-thường-gặp-và-cách-xử-lý-troubleshooting)

---

## 1. Tổng quan hệ thống AI trong FutureCV

Hệ thống FutureCV sử dụng AI cho hai mục đích chính:
1. **Phân tích chất lượng CV (CV Analysis):** Trích xuất thông tin thực thể từ file PDF CV và dùng mô hình ngôn ngữ lớn (LLM) để đánh giá điểm mạnh, điểm yếu và gợi ý cải thiện theo chuẩn quốc tế.
2. **So khớp ứng viên với việc làm (Candidate - Job Matching):** Sử dụng thuật toán đa tiêu chí (Kỹ năng, Kinh nghiệm, Học vấn) kết hợp cùng mô hình nhúng ngữ nghĩa (**Embedding**) và LLM để giải thích độ phù hợp.

Dịch vụ AI được viết bằng **Python FastAPI**, chạy ở cổng `http://localhost:8000`, độc lập với máy chủ web ASP.NET Core.

---

## 2. Hướng dẫn lấy Google Gemini API Key (Miễn phí)

Google cung cấp hạn mức miễn phí (Free Tier) cho các lập trình viên sử dụng mô hình Gemini qua **Google AI Studio**.

### **Các bước thực hiện:**

1. **Truy cập Google AI Studio:**
   * Mở trình duyệt và truy cập: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. **Đăng nhập:**
   * Đăng nhập bằng tài khoản Google (Gmail) cá nhân của bạn.
3. **Tạo API Key mới:**
   * Nhấn vào nút **"Create API key"** (Tạo khóa API).
   * Trong hộp thoại xuất hiện:
     * Chọn **"Create API key in new project"** (nếu bạn chưa có Google Cloud Project nào).
     * Hoặc chọn một project có sẵn trong danh sách.
   * Nhấn **Create**.
4. **Sao chép và lưu trữ Key:**
   * Một chuỗi ký tự dài sẽ hiển thị (thường bắt đầu bằng `AIzaSy...` hoặc định dạng mã hóa Google API).
   * Nhấn nút **Copy** để sao chép key và lưu vào nơi an toàn.

> [!TIP]
> **Tách riêng 2 Key (Tùy chọn nâng cao):**
> Bạn có thể tạo **2 API key riêng biệt**: một key cho tác vụ ngôn ngữ (**LLM**) và một key cho tác vụ nhúng ngữ nghĩa (**Embedding**) để tránh bị nghẽn hạn ngạch (Rate Limit Quota).

---

## 3. Hướng dẫn lấy OpenAI API Key (Tùy chọn)

Nếu bạn muốn chuyển sang sử dụng mô hình của OpenAI (ví dụ: `gpt-4o-mini` và `text-embedding-3-small`):

1. Truy cập trang quản trị khóa của OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Đăng nhập tài khoản OpenAI của bạn (yêu cầu tài khoản đã nạp sẵn số dư Billing tối thiểu $5).
3. Bấm **"Create new secret key"**, đặt tên gợi nhớ (ví dụ: `FutureCV-Dev`) và sao chép mã khóa (bắt đầu bằng `sk-...`).

---

## 4. Cấu hình biến môi trường (`backend-ai/.env`)

Trong thư mục `backend-ai`, tạo file `.env` (hoặc sao chép từ `.env.example`).

### 4.1. Cấu hình chuẩn khuyến nghị (Google Gemini):

```env
APP_NAME=FutureCV Backend AI
ENV=development

HOST=127.0.0.1
PORT=8000

# ── 1. Cấu hình LLM (Phân tích CV & Giải thích Matching) ──
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
GEMINI_LLM_API_KEY=AIzaSy_Dien_Key_LLM_Cua_Ban_Vao_Day

# ── 2. Cấu hình Embedding (Đo tương đồng ngữ nghĩa) ───────
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_API_KEY=AIzaSy_Dien_Key_Embedding_Vao_Day

# Chế độ Embedding: "advisory" (an toàn, chỉ bổ sung metadata, không làm lệch điểm chính)
SEMANTIC_MODE=advisory

# Thuật toán matching ổn định
MATCHING_ALGORITHM=matching-v0

# ── 3. Key dự phòng chung (Fallback nếu không tách riêng) ─
GEMINI_API_KEY=

# ── 4. Khóa bảo mật giao tiếp nội bộ với .NET Backend ────
INTERNAL_API_KEY=futurecv-demo-local-2026

# ── 5. Giới hạn thời gian chờ và thử lại ─────────────────
LLM_TIMEOUT_SECONDS=25
LLM_MAX_RETRIES=1
```

### 4.2. Quy tắc nạp khóa của hệ thống (Key Resolution Rules):
* **Tác vụ LLM (CV Analysis / Match Explanation):**
  1. Ưu tiên đọc `GEMINI_LLM_API_KEY`.
  2. Nếu để trống, tự động fallback sang `GEMINI_API_KEY`.
* **Tác vụ Embedding:**
  1. Ưu tiên đọc `GEMINI_EMBEDDING_API_KEY`.
  2. Nếu để trống, tự động fallback sang `GEMINI_API_KEY`.
* *Nếu bạn chỉ có 1 API Key duy nhất:* Bạn có thể điền cùng một key đó vào cả `GEMINI_LLM_API_KEY` và `GEMINI_EMBEDDING_API_KEY`, hoặc điền vào `GEMINI_API_KEY`.

> [!WARNING]
> **Các model Gemini đang được hỗ trợ:**
> * `gemini-3.5-flash-lite` (Khuyên dùng nhất: tốc độ cực nhanh, nhẹ quota, phản hồi ~1.5s).
> * `gemini-flash-latest` (Phiên bản mới nhất của dòng Flash).
> * `gemini-3.6-flash` (Bản đầy đủ chất lượng cao).
> * **KHÔNG** sử dụng `gemini-2.5-flash` vì Google đã ngừng tiếp nhận người dùng mới cho model này (trả về lỗi `404 NOT_FOUND`).

---

## 5. Đồng bộ cấu hình với ASP.NET Core Backend

Để .NET Backend (`backend/src/FutureCV.Api`) có thể gọi sang FastAPI và gửi dữ liệu CV/Job, bạn cần đảm bảo các thông số trong file `appsettings.Development.json` trùng khớp:

📁 **Đường dẫn file:** `backend/src/FutureCV.Api/appsettings.Development.json`

```json
{
  "AiMatching": {
    "PreviewShadowEnabled": false,
    "PreviewAiEnabled": true
  },
  "AiService": {
    "BaseUrl": "http://localhost:8000",
    "ApiKey": "futurecv-demo-local-2026",
    "TimeoutSeconds": 90
  }
}
```

> [!IMPORTANT]
> Giá trị `"ApiKey"` trong `appsettings.Development.json` **bắt buộc phải khớp 100%** với giá trị `INTERNAL_API_KEY` trong file `backend-ai/.env` (mặc định là `futurecv-demo-local-2026`). Nếu sai khác, request sẽ bị chặn với mã lỗi `401 Unauthorized`.

---

## 6. Kiểm tra hoạt động sau khi cấu hình

### Bước 1: Khởi động FastAPI Server
Mở một cửa sổ Terminal (PowerShell):
```powershell
cd "d:\My Project\CDTH\FutureCV\backend-ai"
# Kích hoạt môi trường ảo nếu có
.\.venv\Scripts\Activate.ps1
# Khởi chạy server
python -m uvicorn app.main:app --port 8000 --reload
```

Server khởi động thành công sẽ hiển thị log:
```text
INFO: Application startup complete.
INFO: Starting FutureCV Backend AI [env=development, provider=gemini, model=gemini-3.5-flash-lite]
```

### Bước 2: Kiểm tra Health Check
Mở cửa sổ Terminal thứ hai và chạy:
```powershell
curl.exe -s http://localhost:8000/api/v1/health
```
Kết quả mong đợi:
```json
{"status":"ok"}
```

### Bước 3: Chạy bộ kiểm thử tự động
Để đảm bảo tất cả chức năng, prompt và thuật toán hoạt động hoàn hảo:
```powershell
cd "d:\My Project\CDTH\FutureCV\backend-ai"
pytest
```
Kết quả mong đợi: **574 passed** (100% Passed).

---

## 7. Các lỗi thường gặp và cách xử lý (Troubleshooting)

| Hiện tượng / Mã lỗi | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **CV chỉ được 10/100 điểm, nhận xét là sinh viên mới ra trường** | FastAPI chưa bật hoặc gọi Gemini lỗi, .NET tự động rơi vào Rule-based Fallback trên dữ liệu rỗng. | 1. Bật `uvicorn`.<br>2. Kiểm tra lại API key trong `.env`.<br>3. Bấm nút **"Chấm lại"** trên trang `candidate/my-cvs`. |
| **HTTP 502 Bad Gateway / `AI_PROVIDER_ERROR`** | Tên model Gemini không hợp lệ (ví dụ: dùng `gemini-2.5-flash` đã bị Google khai tử). | Đổi `LLM_MODEL=gemini-3.5-flash-lite` trong file `.env` và khởi động lại uvicorn. |
| **HTTP 401 Unauthorized** | Mã `X-Internal-API-Key` giữa .NET và FastAPI không giống nhau. | Kiểm tra `INTERNAL_API_KEY` trong `.env` và `AiService:ApiKey` trong `appsettings.Development.json` phải trùng nhau. |
| **Lỗi `429 RESOURCE_EXHAUSTED`** | Đã gọi vượt quá số lượng request miễn phí của Google (Rate Limit). | Chờ 1-2 phút hoặc chuyển sang dùng 2 key riêng biệt cho LLM và Embedding. |
| **Lỗi 500 khi xem chi tiết việc làm trên web** | Trường `VerifiedStatus` trong database có giá trị cũ (`Unverified`). | Chạy lệnh SQL: `UPDATE "Companies" SET "VerifiedStatus" = 'Verified';` trong PostgreSQL. |

---

> [!CAUTION]
> **Bảo mật mã khóa:** File `.env` chứa thông tin nhạy cảm đã được liệt kê trong `.gitignore`. Tuyệt đối không xóa `.gitignore` hoặc commit file `.env` lên kho lưu trữ GitHub công khai.

