import type { ReactNode } from "react";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { Skeleton } from "~/components/ui/Skeleton";
import { EmptyState } from "~/components/ui/EmptyState";
import { Button } from "~/components/ui/Button";
import { ApiError } from "~/lib/fetcher";
import { translateErrorMessage } from "~/lib/errorMapper";

interface QueryBoundaryProps {
  isLoading: boolean;
  error?: unknown;
  onRetry?: () => void;
  /** Skeleton khớp layout của nội dung (không dùng spinner tròn). */
  skeleton: ReactNode;
  children: ReactNode;
}

export function QueryBoundary({ isLoading, error, onRetry, skeleton, children }: QueryBoundaryProps) {
  const { reset } = useQueryErrorResetBoundary();

  if (isLoading) return <>{skeleton}</>;

  if (error) {
    let message = "Không thể tải dữ liệu. Kiểm tra kết nối và thử lại.";
    if (error instanceof ApiError) {
      if (error.isNetworkError) {
        message = "Mất kết nối tới máy chủ. Kiểm tra mạng và thử lại.";
      } else if (error.status === 401) {
        message = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
      } else if (error.status >= 500) {
        message = "Máy chủ đang gặp sự cố. Vui lòng thử lại sau ít phút.";
      } else {
        message = translateErrorMessage(error.message, error.status);
      }
    } else if (error instanceof Error) {
      message = translateErrorMessage(error.message);
    }

    return (
      <EmptyState
        title="Đã xảy ra lỗi"
        description={message}
        action={
          onRetry && (
            <Button
              variant="secondary"
              onClick={() => {
                reset();
                onRetry();
              }}
            >
              Thử lại
            </Button>
          )
        }
      />
    );
  }

  return <>{children}</>;
}

/** Skeleton khối generic dùng ghép các layout khớp nội dung. */
export function SkeletonCard({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={`flex flex-col gap-3 rounded-default border border-border-subtle bg-surface p-6 ${className ?? ""}`}>
      <Skeleton className="h-6 w-2/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
      <Skeleton className="h-4 w-1/3" />
    </div>
  );
}
