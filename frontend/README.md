# FutureCV — Frontend

> **Tech Stack:** React 19 · React Router v8 · Zustand v5 · TanStack Query v5 · TypeScript · Tailwind CSS v4 · Vite

---

## Mục lục

1. [Tổng quan kiến trúc](#tổng-quan-kiến-trúc)
2. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
3. [Nhiệm vụ từng folder](#nhiệm-vụ-từng-folder)
4. [Data Fetching — TanStack Query](#data-fetching--tanstack-query)
5. [Quy tắc đặt file](#quy-tắc-đặt-file)
6. [Scripts](#scripts)
7. [Môi trường phát triển](#môi-trường-phát-triển)

> 📖 Xem thêm: [ROUTER_AND_ZUSTAND.md](./ROUTER_AND_ZUSTAND.md) — Giải thích chi tiết về React Router v8 SPA Mode và Zustand.

---

## Tổng quan kiến trúc

Dự án theo mô hình **Feature-Based Architecture** kết hợp với **SPA Mode** của React Router v8.  
Toàn bộ render xảy ra trên **client (trình duyệt)**, không có server-side rendering.

```
Browser Request
      │
      ▼
 React Router v8 (SPA Mode — ssr: false)
      │
      ├─ PublicLayout    ──► Home, About, Contact
      ├─ AuthLayout      ──► Login, Register, Forgot Password
      ├─ CandidateLayout ──► Dashboard, Jobs, Profile, Apply
      ├─ HRLayout        ──► Job Management, Pipeline, Interview
      └─ AdminLayout     ──► User Mgmt, Role, System Config
            │
            ▼
       Zustand Stores
       ├─ useAuthStore   ──► user, token, role, isAuthenticated
       └─ useUIStore     ──► isLoading, modal, toast
            │
            ▼
      TanStack Query     ──► Cache + fetch qua fetcher.ts
            │
            ▼
        Backend API
```

---

## Cấu trúc thư mục

```
frontend/
├── app/
│   ├── root.tsx                  # Root component — mount toàn bộ app
│   ├── routes.ts                 # Khai báo route tree (React Router v8)
│   ├── app.css                   # CSS global entry (Tailwind)
│   │
│   ├── routes/                   # 📄 Page files (thin layer)
│   │   ├── public/
│   │   ├── auth/
│   │   ├── candidate/
│   │   ├── hr/
│   │   └── admin/
│   │
│   ├── layouts/                  # 🏗️ Layout wrapper cho từng role
│   │   ├── PublicLayout.tsx
│   │   ├── AuthLayout.tsx
│   │   ├── CandidateLayout.tsx
│   │   ├── HRLayout.tsx
│   │   └── AdminLayout.tsx
│   │
│   ├── features/                 # 🧩 Business logic theo domain
│   │   ├── auth/
│   │   ├── candidate/
│   │   ├── hr/
│   │   └── admin/
│   │
│   ├── components/               # 🔧 Component dùng chung
│   │   ├── ui/                   #   Primitive UI (Button, Input, Modal, Table)
│   │   └── shared/               #   Avatar, StatusBadge, QueryBoundary
│   │
│   ├── stores/                   # 🗃️ Zustand global stores
│   │   ├── useAuthStore.ts
│   │   └── useUIStore.ts
│   │
│   ├── guards/                   # 🔐 Route guards (chạy trong clientLoader)
│   │   ├── requireAuth.ts
│   │   └── requireRole.ts
│   │
│   ├── lib/                      # ⚙️ Cấu hình thư viện
│   │   ├── fetcher.ts
│   │   ├── queryClient.ts
│   │   └── queryKeys.ts
│   │
│   ├── hooks/                    # 🪝 Custom hooks dùng chung
│   │   ├── useDebounce.ts
│   │   └── useWindowSize.ts
│   │
│   ├── types/                    # 📐 Types/Interfaces dùng chung
│   │   └── index.ts
│   │
│   ├── utils/                    # 🛠️ Pure helper functions
│   │   └── index.ts
│   │
│   └── styles/                   # 🎨 CSS variables / theme
│
├── public/                       # Static assets
├── react-router.config.ts        # ⚠️ ssr: false (SPA Mode)
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## Nhiệm vụ từng folder

### `routes/` — Trang (Page files)

**Quy tắc:** Route file phải **gọn nhất có thể**. Chỉ làm 2 việc:
1. Export `clientLoader` để gọi guard
2. Render component từ `features/`

```tsx
// ✅ Đúng
import { CandidateDashboardPage } from '~/features/candidate/components/CandidateDashboardPage';
import { requireRole } from '~/guards/requireRole';

export async function clientLoader() {
  requireRole(['candidate']);
}

export default function DashboardRoute() {
  return <CandidateDashboardPage />;
}
```

| Folder | Trang |
|--------|-------|
| `routes/public/` | home, about, contact, not-found |
| `routes/auth/` | login, register, forgot-password |
| `routes/candidate/` | dashboard, job-list, job-detail, apply-form, profile |
| `routes/hr/` | dashboard, job-management, candidate-pipeline, interview |
| `routes/admin/` | dashboard, user-management, role-permission, system-config |

---

### `layouts/` — Layout wrapper

Mỗi layout bọc toàn bộ trang của một nhóm role. Layout chứa Navbar, Sidebar, Header... không chứa business logic.

| File | Dùng cho |
|------|---------|
| `PublicLayout.tsx` | Navbar + Footer cho khách vãng lai |
| `AuthLayout.tsx` | Centered form layout cho login/register |
| `CandidateLayout.tsx` | Sidebar + Header cho ứng viên |
| `HRLayout.tsx` | Sidebar + Header cho HR |
| `AdminLayout.tsx` | Sidebar + Header cho Admin |

---

### `features/` — Business logic theo domain

Đây là **nơi chứa phần lớn code**. Mỗi feature có cấu trúc nhất quán:

```
features/{domain}/
├── components/   # UI components của domain này
├── hooks/        # Custom hooks (useLogin, useApplyJob, ...)
├── queries/      # TanStack Query hooks (useJobListQuery, ...)
├── services/     # Hàm gọi API (candidateApi.ts, authApi.ts, ...)
└── types/        # Types/Interfaces riêng của domain
```

| Feature | Domain |
|---------|--------|
| `features/auth/` | Đăng nhập, đăng ký, quên mật khẩu |
| `features/candidate/` | Xem việc, nộp đơn, quản lý hồ sơ |
| `features/hr/` | Đăng tin, quản lý pipeline, phỏng vấn |
| `features/admin/` | Quản lý user, phân quyền, cấu hình hệ thống |

---

### `components/` — Component tái sử dụng

| Folder | Quy tắc |
|--------|---------|
| `components/ui/` | Pure UI — **không import store, không gọi API**. Chỉ nhận props. |
| `components/shared/` | Có thể dùng store/query nhẹ. Dùng ở nhiều feature khác nhau. |

---

### `stores/` — Zustand global state

Chỉ chứa **global state** thực sự cần dùng ở nhiều nơi. State cục bộ của một component để trong `useState`.

| Store | Chứa gì |
|-------|---------|
| `useAuthStore.ts` | `user`, `token`, `role`, `isAuthenticated`, `setAuth()`, `logout()` |
| `useUIStore.ts` | `isLoading`, `modalOpen`, `toastQueue`, các setter tương ứng |

> Xem code mẫu chi tiết tại [ROUTER_AND_ZUSTAND.md](./ROUTER_AND_ZUSTAND.md)

---

### `guards/` — Bảo vệ route

Guards được gọi trong `clientLoader` của route file. Dùng `useAuthStore.getState()` (không phải hook).

| File | Chức năng |
|------|-----------|
| `requireAuth.ts` | Redirect về `/login` nếu chưa đăng nhập |
| `requireRole.ts` | Redirect nếu không đúng role |

---

### `lib/` — Cấu hình thư viện

| File | Vai trò |
|------|---------|
| `fetcher.ts` | Axios instance, tự động gắn `Authorization: Bearer <token>` |
| `queryClient.ts` | Khởi tạo TanStack `QueryClient` dùng chung toàn app |
| `queryKeys.ts` | Factory tạo query key — tránh hardcode string |

---

### `hooks/`, `types/`, `utils/`

| Folder | Nội dung |
|--------|---------|
| `hooks/` | Custom hooks **không thuộc feature nào** (`useDebounce`, `useWindowSize`) |
| `types/` | Types dùng chung: `ApiResponse<T>`, `PaginatedData<T>`, `Role`, ... |
| `utils/` | Pure functions: `formatDate()`, `truncate()`, `cn()`, ... |

---

## Data Fetching — TanStack Query

Không bao giờ gọi API trực tiếp trong component. Luồng bắt buộc:

```
Component
  └── useQuery / useMutation
        └── features/{domain}/queries/use___Query.ts
              └── features/{domain}/services/___Api.ts
                    └── lib/fetcher.ts
                          └── Backend API
```

**Query Keys tập trung tại `lib/queryKeys.ts`:**
```ts
export const queryKeys = {
  jobs: {
    all:    () => ['jobs'] as const,
    list:   (f: JobFilter) => ['jobs', 'list', f] as const,
    detail: (id: string)   => ['jobs', 'detail', id] as const,
  },
  candidate: {
    profile:      () => ['candidate', 'profile'] as const,
    applications: () => ['candidate', 'applications'] as const,
  },
};
```

---

## Quy tắc đặt file

| Tình huống | Đặt ở đâu |
|-----------|-----------|
| Gọi API lấy danh sách jobs | `features/candidate/services/candidateApi.ts` |
| Hook `useJobList` dùng TanStack Query | `features/candidate/queries/useJobListQuery.ts` |
| Component `JobCard` | `features/candidate/components/JobCard.tsx` |
| `Button` dùng mọi nơi | `components/ui/Button.tsx` |
| `Avatar` dùng ở nhiều feature | `components/shared/Avatar.tsx` |
| `useDebounce` không thuộc feature | `hooks/useDebounce.ts` |
| Type `Job`, `Application` | `features/candidate/types/index.ts` |
| Type `ApiResponse<T>` dùng chung | `types/index.ts` |
| Helper `formatDate()` | `utils/index.ts` |

---

## Scripts

```bash
npm run dev         # Dev server tại localhost:5173
npm run build       # Build production (output: build/)
npm run start       # Serve production build
npm run typecheck   # Kiểm tra TypeScript
```

---

## Môi trường phát triển

**Yêu cầu:** Node.js >= 20, npm >= 10

```bash
cd frontend
npm install
npm run dev
```

**Biến môi trường** — tạo file `.env`:
```env
VITE_API_BASE_URL=http://localhost:8080/api
```

> Tất cả biến môi trường Vite phải có prefix `VITE_`.  
> Truy cập: `import.meta.env.VITE_API_BASE_URL`
