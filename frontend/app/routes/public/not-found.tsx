import { Link, isRouteErrorResponse, useRouteError } from "react-router";
import { Button } from "~/components/ui/Button";

export default function NotFoundPage() {
  const error = useRouteError();
  const is404 = isRouteErrorResponse(error) && error.status === 404;

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-margin-mobile py-24 text-center">
      <p className="text-display font-bold text-navy/10">{is404 ? "404" : "Lỗi"}</p>
      <h1 className="mt-2 text-headline text-navy">
        {is404 ? "Không tìm thấy trang" : "Đã xảy ra lỗi"}
      </h1>
      <p className="mt-3 max-w-md text-ink-variant">
        {is404
          ? "Trang bạn tìm kiếm không tồn tại hoặc đã bị di chuyển."
          : "Có lỗi không mong muốn khi hiển thị trang này."}
      </p>
      <div className="mt-8 flex gap-4">
        <Button variant="primary" onClick={() => window.history.back()}>
          Quay lại
        </Button>
        <Link
          to="/"
          className="inline-flex h-11 items-center rounded-default border border-navy px-6 font-semibold text-navy transition-colors hover:bg-navy hover:text-white"
        >
          Về trang chủ
        </Link>
      </div>
    </div>
  );
}
