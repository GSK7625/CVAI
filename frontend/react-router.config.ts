import type { Config } from "@react-router/dev/config";

export default {
  // ⚠️ SPA Mode - SSR bị tắt để tương thích với Zustand
  // Zustand store chạy hoàn toàn phía client-side.
  // Nếu bật ssr: true, Zustand sẽ bị hydration mismatch vì
  // server không có window/localStorage và store state không
  // được serialize/deserialize giữa server → client.
  ssr: false,
} satisfies Config;
