import {
  isRouteErrorResponse,
  Links,
  Meta,
  Navigate,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
} from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";

import type { Route } from "./+types/root";
import { queryClient } from "~/lib/queryClient";
import { translateErrorMessage } from "~/lib/errorMapper";
import { ToastViewport } from "~/components/ui";
import { useAuthStore } from "~/stores/useAuthStore";
import { getHrWorkspaceRedirect } from "~/guards/hrWorkspace";
import "@fontsource-variable/hanken-grotesk";
import "./app.css";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

function HrWorkspaceBoundary({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((state) => state.user?.role);
  const { pathname } = useLocation();
  const redirectTo = getHrWorkspaceRedirect(role, pathname);
  return redirectTo ? <Navigate to={redirectTo} replace /> : children;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HrWorkspaceBoundary>
        <Outlet />
      </HrWorkspaceBoundary>
      <ToastViewport />
    </QueryClientProvider>
  );
}

export default App;

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Đã xảy ra lỗi";
  let details = "Có lỗi không mong muốn khi hiển thị trang này.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : `Lỗi ${error.status}`;
    details =
      error.status === 404
        ? "Trang bạn tìm kiếm không tồn tại hoặc đã bị di chuyển."
        : translateErrorMessage(error.statusText, error.status);
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = translateErrorMessage(error.message);
    stack = error.stack;
  }

  return (
    <HrWorkspaceBoundary>
      <main className="container-page mx-auto px-margin-mobile md:px-margin-desktop py-24">
        <h1 className="text-headline text-navy">{message}</h1>
        <p className="mt-2 text-ink-variant">{details}</p>
        {stack && (
          <pre className="mt-6 w-full overflow-x-auto rounded-default bg-surface-low p-4 text-label-sm">
            <code>{stack}</code>
          </pre>
        )}
      </main>
    </HrWorkspaceBoundary>
  );
}

export const meta: Route.MetaFunction = () => [
  { title: "FutureCV - Việc làm & Tạo CV Online" },
  {
    name: "description",
    content:
      "FutureCV: tìm kiếm việc làm phù hợp, tạo CV online chuyên nghiệp và tuyển dụng hiệu quả.",
  },
];
