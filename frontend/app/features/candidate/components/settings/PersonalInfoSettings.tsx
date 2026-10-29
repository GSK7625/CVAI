import { useState, useEffect, useRef } from "react";
import {
  IconDeviceFloppy,
  IconAlertCircle,
  IconRefresh,
  IconCamera,
  IconLoader2,
  IconUpload,
} from "@tabler/icons-react";
import { useCandidateProfile } from "~/features/candidate/hooks/useCandidateProfile";
import { useUpdateCandidateProfile } from "~/features/candidate/hooks/useUpdateCandidateProfile";
import { useUploadCandidateAvatar } from "~/features/candidate/hooks/useUploadCandidateAvatar";
import { useUIStore } from "~/stores/useUIStore";
import { Button } from "~/components/ui/Button";
import { Input, Field } from "~/components/ui/Input";
import { Skeleton } from "~/components/ui/Skeleton";
import { Avatar } from "~/components/ui/Avatar";
import { cn } from "~/lib/cn";

export function PersonalInfoSettings() {
  const showToast = useUIStore((s) => s.showToast);
  const { profile, displayName, avatarUrl, isLoading, isError, refetch } = useCandidateProfile();
  const updateMutation = useUpdateCandidateProfile();
  const uploadAvatarMutation = useUploadCandidateAvatar();
  const avatarInputRef = useRef<HTMLInputElement>(null);

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ fullName?: string; phone?: string }>({});

  const handleAvatarFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";

    const validMimeTypes = ["image/jpeg", "image/png", "image/jpg"];
    const validExtensions = [".jpg", ".jpeg", ".png"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validMimeTypes.includes(file.type.toLowerCase()) && !validExtensions.includes(ext)) {
      showToast("Ảnh đại diện phải có định dạng JPG hoặc PNG.", "error");
      return;
    }

    const maxSizeBytes = 5 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      showToast("Kích thước ảnh đại diện không được vượt quá 5MB.", "error");
      return;
    }

    try {
      await uploadAvatarMutation.mutateAsync(file);
      showToast("Cập nhật ảnh đại diện thành công!", "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Tải ảnh đại diện thất bại";
      showToast(message, "error");
    }
  };

  // Đồng bộ form state khi profile load xong từ API
  useEffect(() => {
    if (profile) {
      setFullName(profile.fullName || "");
      setPhone(profile.phone || "");
    }
  }, [profile]);

  // Chuẩn hóa số điện thoại: loại bỏ khoảng trắng, dấu gạch ngang, dấu chấm, đổi +84 về 0
  const normalizePhone = (raw: string): string => {
    let cleaned = raw.trim().replace(/[\s\-\.]/g, "");
    if (cleaned.startsWith("+84")) {
      cleaned = "0" + cleaned.slice(3);
    }
    return cleaned;
  };

  const validate = () => {
    const errors: { fullName?: string; phone?: string } = {};
    if (!fullName.trim()) {
      errors.fullName = "Họ và tên không được để trống";
    }
    if (phone.trim()) {
      const cleanPhone = normalizePhone(phone);
      if (!/^0\d{9}$/.test(cleanPhone)) {
        errors.phone = "Số điện thoại không hợp lệ (cần đúng 10 số bắt đầu bằng 0, ví dụ: 0912345678)";
      }
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const cleanPhone = phone.trim() ? normalizePhone(phone) : undefined;

    try {
      await updateMutation.mutateAsync({
        fullName: fullName.trim(),
        phone: cleanPhone,
      });
      if (cleanPhone) setPhone(cleanPhone);
      showToast("Cập nhật thông tin cá nhân thành công", "success");
    } catch (err) {
      let message = err instanceof Error ? err.message : "Cập nhật thông tin thất bại";
      if (
        message.includes("Phone number must be a valid Vietnamese number") ||
        message.includes("Số điện thoại không hợp lệ")
      ) {
        message = "Số điện thoại không hợp lệ (cần đúng 10 số bắt đầu bằng 0, ví dụ: 0912345678)";
        setFieldErrors((prev) => ({ ...prev, phone: message }));
      }
      showToast(message, "error");
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* Outer Shell (Double-Bezel) */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        {/* Inner Core */}
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="border-b border-border-subtle pb-5">
            <h1 className="text-headline-md font-bold text-navy">Cài đặt thông tin cá nhân</h1>
            <p className="mt-1 text-label-sm font-medium text-danger">(*) Các thông tin bắt buộc</p>
          </div>

          {isLoading ? (
            <div className="space-y-6 pt-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-10 w-full rounded-default" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full rounded-default" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-10 w-full rounded-default" />
              </div>
              <Skeleton className="h-10 w-28 rounded-default" />
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger mb-3">
                <IconAlertCircle size={24} stroke={2} />
              </div>
              <h2 className="text-body font-semibold text-navy">Không thể tải thông tin hồ sơ</h2>
              <p className="mt-1 max-w-sm text-body-sm text-ink-muted">
                Đã xảy ra lỗi khi kết nối với máy chủ. Vui lòng kiểm tra lại kết nối mạng.
              </p>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => refetch()}
                className="mt-4 gap-2 border-border-strong"
              >
                <IconRefresh size={16} stroke={1.8} />
                Thử lại
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6 pt-6">
              {/* Ảnh đại diện */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5 rounded-xl border border-border-subtle bg-surface-low/50 p-4">
                <input
                  ref={avatarInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  className="hidden"
                  onChange={handleAvatarFileChange}
                />
                <div className="relative group shrink-0">
                  <Avatar
                    src={avatarUrl}
                    name={displayName}
                    size="lg"
                    className="border-2 border-surface shadow-md"
                  />
                  <button
                    type="button"
                    onClick={() => avatarInputRef.current?.click()}
                    disabled={uploadAvatarMutation.isPending}
                    title="Đổi ảnh đại diện"
                    aria-label="Đổi ảnh đại diện"
                    className={cn(
                      "absolute inset-0 flex items-center justify-center rounded-full bg-navy/60 text-white transition-opacity duration-200",
                      uploadAvatarMutation.isPending
                        ? "opacity-100 cursor-wait"
                        : "opacity-0 group-hover:opacity-100 cursor-pointer",
                    )}
                  >
                    {uploadAvatarMutation.isPending ? (
                      <IconLoader2 size={24} className="animate-spin text-gold" />
                    ) : (
                      <IconCamera size={24} stroke={1.8} />
                    )}
                  </button>
                </div>
                <div className="min-w-0 flex-1 space-y-1.5">
                  <h3 className="text-label font-semibold text-navy">Ảnh đại diện</h3>
                  <p className="text-label-sm text-ink-muted">
                    Hỗ trợ định dạng JPG, PNG. Dung lượng tối đa 5MB. Ảnh sẽ được tối ưu tự động và hiển thị trên hồ sơ của bạn.
                  </p>
                  <div className="pt-1">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={uploadAvatarMutation.isPending}
                      onClick={() => avatarInputRef.current?.click()}
                      className="gap-2 border-border-strong text-navy hover:border-gold hover:text-gold"
                    >
                      {uploadAvatarMutation.isPending ? (
                        <>
                          <IconLoader2 size={16} className="animate-spin text-gold" />
                          <span>Đang tải lên...</span>
                        </>
                      ) : (
                        <>
                          <IconUpload size={16} stroke={1.8} />
                          <span>Tải ảnh mới</span>
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
              <Field
                label="Họ và tên"
                required
                error={fieldErrors.fullName}
                htmlFor="personal-fullname"
              >
                <Input
                  id="personal-fullname"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (fieldErrors.fullName) setFieldErrors((prev) => ({ ...prev, fullName: undefined }));
                  }}
                  placeholder="Nhập họ và tên"
                  aria-required="true"
                  className="bg-surface focus:border-gold focus:ring-gold"
                />
              </Field>

              <Field
                label="Số điện thoại"
                error={fieldErrors.phone}
                htmlFor="personal-phone"
              >
                <Input
                  id="personal-phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => {
                    setPhone(e.target.value);
                    if (fieldErrors.phone) setFieldErrors((prev) => ({ ...prev, phone: undefined }));
                  }}
                  placeholder="Ví dụ: 0912345678"
                  className="bg-surface focus:border-gold focus:ring-gold"
                />
              </Field>

              <Field
                label="Email"
                htmlFor="personal-email"
              >
                <Input
                  id="personal-email"
                  type="email"
                  value={profile?.email || ""}
                  disabled
                  readOnly
                  aria-disabled="true"
                  className="cursor-not-allowed bg-surface-low text-ink-muted border-border-subtle opacity-80"
                />
                <p className="mt-1.5 text-label-sm text-ink-muted">
                  Email tài khoản không thể thay đổi trực tiếp.
                </p>
              </Field>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="min-w-[120px] rounded-lg bg-navy px-6 py-2.5 text-label font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {updateMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang lưu...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <IconDeviceFloppy size={18} stroke={1.8} />
                      Lưu
                    </span>
                  )}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
