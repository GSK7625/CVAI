# 🤖 FutureCV Backend AI (Python FastAPI - Clean & Hexagonal Architecture)

Tài liệu hướng dẫn cấu trúc, thiết lập và phát triển hệ thống tính toán trí tuệ nhân tạo (**AI Service**) của dự án **FutureCV**.

> 💡 **Hướng dẫn cấu hình API Key & Môi trường:** Xem chi tiết từng bước tại [API_KEY_CONFIGURATION_GUIDE.md](./API_KEY_CONFIGURATION_GUIDE.md).

---

## 🏛️ 1. Kiến trúc hệ thống (Clean & Hexagonal Architecture)

Hệ thống FutureCV tuân thủ mô hình **Modular Monolith**, trong đó **ASP.NET Core** đóng vai trò là Application Server trung tâm điều phối, còn **Python FastAPI** đóng vai trò là một **Stateless AI Compute Service** (Dịch vụ tính toán AI phi trạng thái):

```text
               ┌───────────────────────┐
               │    React Frontend     │
               └──────────┬────────────┘
                          │ HTTPS / REST (Public Client)
                          ▼
               ┌───────────────────────┐
               │  ASP.NET Core Backend │
               │   (Modular Monolith)  │
               └──────┬──────────┬─────┘
                      │          │
         PostgreSQL ──┘          │ Internal REST (X-Internal-API-Key)
                                 ▼
                      ┌───────────────────────┐
                      │    Python FastAPI     │
                      │      AI Service       │
                      │  (Stateless Compute)  │
                      └──────────┬────────────┘
                                 │
                                 ▼
                     LLM & Embedding Providers
                   (OpenAI / Gemini / Mock Local)
```

### 🔒 Các nguyên tắc bất biến (Strict System Invariants):
1. **Frontend KHÔNG BAO GIỜ gọi thẳng FastAPI:** Trình duyệt chỉ giao tiếp với ASP.NET Core; FastAPI đã tắt Browser CORS.
2. **FastAPI KHÔNG kết nối Database:** Toàn bộ dữ liệu được lưu trữ và quản lý bởi ASP.NET Core qua PostgreSQL; FastAPI không sử dụng bất kỳ ORM nào (không SQLAlchemy, không psycopg).
3. **Hoàn toàn phi trạng thái (Stateless):** FastAPI không lưu session, không giữ state của người dùng; cùng dữ liệu đầu vào luôn cho kết quả xử lý độc lập.
4. **Xác thực bảo mật nội bộ:** Mọi request từ ASP.NET Core sang FastAPI được bảo vệ bằng mã khóa bí mật qua header `X-Internal-API-Key` với cơ chế so khớp Constant-time (`hmac.compare_digest`).

---

### 📂 Cấu trúc thư mục mã nguồn

Mã nguồn được tổ chức theo kiến trúc **Hexagonal (Ports & Adapters)** chuẩn mực:

```text
backend-ai/
├── .env.example                 # File mẫu cấu hình biến môi trường
├── requirements.txt             # Danh sách thư viện runtime cho ứng dụng
├── requirements-dev.txt         # Danh sách thư viện phục vụ test và linter
├── pyproject.toml               # Cấu hình tập trung cho Ruff, Mypy, Pytest
├── Dockerfile                   # Cấu hình đóng gói container chạy production
│
├── app/
│   ├── main.py                  # Entry Point của FastAPI application (Lifespan, Middleware)
│   ├── api/                     # [Tầng Giao tiếp API] Router v1, Dependencies, Exception Handlers
│   │   └── v1/                  # Endpoints: CV parsing/analysis, Job Matching, Candidate Ranking, Assistant
│   ├── application/             # [Tầng Dịch vụ Ứng dụng] CvAnalyzerService, MatchingService, RankingService
│   ├── domain/                  # [Tầng Lõi Nghiệp vụ] Logic toán học thuần túy, KHÔNG phụ thuộc framework
│   │   ├── cv/                  # Chấm điểm chất lượng CV (scoring.py), chuẩn hóa kỹ năng (normalization.py)
│   │   └── matching/            # Thuật toán so khớp: skill_match, experience_match, education_match, scoring
│   ├── contracts/               # [Hợp đồng Dữ liệu] Pydantic v2 schemas: StructuredCv, StructuredJob, MatchResult
│   ├── ports/                   # [Interfaces Trừu tượng] LlmPort, EmbeddingPort, DocumentParserPort
│   ├── infrastructure/          # [Tầng Hạ tầng / Adapter] Triển khai gọi OpenAI, Gemini, PyMuPDF, Mock
│   ├── prompts/                 # [Quản lý Prompt AI] Prompt templates có phiên bản (v1) với Delimiters bảo mật
│   ├── core/                    # Cấu hình ứng dụng (Settings), Custom Exceptions, Temporal utils
│   └── observability/           # Structured Logging, Correlation ID tracing
│
├── evaluation/                  # Bộ công cụ đánh giá & Benchmark chất lượng Matching độc lập
└── tests/                       # Hơn 470+ Unit, Integration & Architecture tests tự động
```

---

## ️ 2. Yêu cầu môi trường (Prerequisites)

* **Python 3.11** trở lên (khuyên dùng Python 3.11 hoặc 3.12).
* **Git** để quản lý mã nguồn.
* **IDE/Editor khuyến nghị**: VS Code (cài extension *Python*, *Pylance*, *Ruff*), PyCharm, hoặc Cursor.

---

##  3. Hướng dẫn chạy dự án ở máy Local

### **Bước 1: Chuyển vào thư mục `backend-ai`**
Mở terminal và di chuyển vào thư mục dịch vụ AI:
```bash
cd backend-ai
```

### **Bước 2: Khởi tạo và kích hoạt Môi trường ảo (Virtual Environment)**
- **Trên Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(Nếu gặp lỗi Execution Policy trên PowerShell, chạy trước: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **Trên macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### **Bước 3: Cài đặt các thư viện cần thiết**
Cài đặt toàn bộ dependencies cho runtime và công cụ kiểm thử:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### **Bước 4: Cấu hình Biến môi trường (`.env`)**
1. Sao chép file cấu hình mẫu `.env.example` thành `.env`:
   - **Windows PowerShell:**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **macOS / Linux / Bash:**
     ```bash
     cp .env.example .env
     ```
2. Mở file `.env` vừa tạo để kiểm tra cấu hình:
   - **Chế độ Mặc định (Local Offline - Không cần API Key):**
     ```env
     LLM_PROVIDER=mock
     EMBEDDING_PROVIDER=mock
     MATCHING_ALGORITHM=matching-v0
     INTERNAL_API_KEY=
     ```
     *(Hệ thống sẽ chạy hoàn toàn độc lập ở máy local với Mock Provider mà không tốn tiền API).*
   - **Chế độ Kết nối AI Thật (OpenAI / Gemini):**
     ```env
     LLM_PROVIDER=openai
     OPENAI_API_KEY=sk-...
     EMBEDDING_PROVIDER=openai
     MATCHING_ALGORITHM=matching-v1-experimental
     INTERNAL_API_KEY=futurecv-local-shadow-test
     ```

### **Bước 5: Khởi chạy AI Service**
Chạy ứng dụng bằng máy chủ Uvicorn với chế độ tự động reload khi sửa code:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### **Bước 6: Kiểm tra và truy cập Swagger UI**
Sau khi ứng dụng khởi chạy thành công:
- 👉 **Health Check Probe**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- 👉 **Readiness Check Probe**: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)
- 👉 **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 👉 **Alternative Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🎯 4. Các tính năng cốt lõi & API Endpoints

| Endpoint | Method | Mô tả chức năng |
| :--- | :---: | :--- |
| `/api/v1/cv/parse-pdf` | `POST` | Đọc và bóc tách văn bản thô từ file PDF CV (hỗ trợ file tới 5MB, chặn DoS bộ nhớ). |
| `/api/v1/cv/analyze` | `POST` | Bóc tách thực thể CV (`StructuredCv`), chấm điểm chất lượng CV (0–100) và đưa ra gợi ý cải thiện. |
| `/api/v1/matching/match` | `POST` | So khớp độ phù hợp giữa 1 CV và 1 Tin tuyển dụng (Job), tính điểm và sinh nhận xét chi tiết. |
| `/api/v1/matching/rank-candidates` | `POST` | Xếp hạng hàng loạt ứng viên cho 1 Job với tốc độ cao (tối ưu hóa batching, 0 tốn phí LLM). |
| `/api/v1/assistant/chat` | `POST` | Trợ lý tư vấn lộ trình sự nghiệp thông minh (đã ẩn danh hóa thông tin nhạy cảm PII). |

---

## ⚙️ 5. Quy định phát triển & Tiêu chuẩn chất lượng (Quality Gates)

Toàn bộ mã nguồn trước khi commit hoặc tạo Pull Request phải vượt qua **5 bài kiểm tra chất lượng tự động**:

```bash
# 1. Kiểm tra cú pháp và biên dịch bytecode Python
python -m compileall app tests

# 2. Kiểm tra chất lượng và phong cách mã nguồn (Linter)
python -m ruff check app tests

# 3. Kiểm tra định dạng code tự động (Formatter)
python -m ruff format --check app tests

# 4. Kiểm tra an toàn kiểu dữ liệu tĩnh (Strict Static Type Check)
python -m mypy app

# 5. Chạy toàn bộ bộ kiểm thử tự động (Hơn 470+ Unit & Integration Tests)
python -m pytest tests -v
```

> [!TIP]
> **Tự động sửa lỗi format nhanh:** Bạn có thể chạy lệnh `python -m ruff format app tests` và `python -m ruff check --fix app tests` để công cụ tự động căn chỉnh code chuẩn quy cách PEP 8.

---

## 🛡️ 6. Tiêu chuẩn bảo mật & Phòng vệ dữ liệu

1. **Bảo vệ PII (Personally Identifiable Information):** Họ tên, số điện thoại, email của ứng viên luôn được làm sạch qua bộ lọc `sanitize_free_text` trước khi gửi lên mô hình ngôn ngữ lớn (LLM).
2. **Chống tấn công Prompt Injection:** Toàn bộ nội dung CV và JD được bao bọc trong các thẻ phân tách rõ ràng (`<<<BEGIN UNTRUSTED DATA>>>...<<<END UNTRUSTED DATA>>>`), ngăn chặn các chỉ thị độc hại can thiệp vào hành vi của AI.
3. **Phòng chống DoS tệp tải lên:** File PDF được đọc theo luồng phân đoạn nhỏ (Stream Chunks 64KB) và giới hạn tối đa 5MB, chặn đứng nguy cơ tràn RAM máy chủ.

---

## 🤝 7. Liên hệ & Đóng góp

Nếu gặp bất kỳ khó khăn nào trong quá trình thiết lập môi trường Python hoặc cần tích hợp thêm mô hình AI mới, vui lòng liên hệ thành viên phụ trách AI Module hoặc tạo issue trên repository dự án.
