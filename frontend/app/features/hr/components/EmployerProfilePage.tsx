import { useEffect, useState, type FormEvent } from "react";
import { IconCamera, IconId } from "@tabler/icons-react";
import { Avatar, Button, Card, CardContent, Field, Input } from "~/components/ui";
import { QueryBoundary, SkeletonCard } from "~/components/shared/QueryBoundary";
import { useUIStore } from "~/stores/useUIStore";
import { validateEmployerProfile, type FieldErrors } from "../contracts/hrContracts";
import {
  useEmployerProfile,
  useUpdateEmployerProfile,
  useUploadEmployerAvatar,
} from "../hooks/useEmployerProfile";
import type { EmployerProfileInput } from "../types";

const emptyForm: EmployerProfileInput = { fullName: "", position: "", gender: "", phone: "" };

export function EmployerProfilePage() {
  const profileQuery = useEmployerProfile();
  const updateProfile = useUpdateEmployerProfile();
  const uploadAvatar = useUploadEmployerAvatar();
  const showToast = useUIStore((state) => state.showToast);
  const [values, setValues] = useState(emptyForm);
  const [errors, setErrors] = useState<FieldErrors<EmployerProfileInput>>({});

  useEffect(() => {
    if (!profileQuery.data) return;
    setValues({
      fullName: profileQuery.data.fullName,
      position: profileQuery.data.position ?? "",
      gender: profileQuery.data.gender ?? "",
      phone: profileQuery.data.phone ?? "",
    });
  }, [profileQuery.data]);

  const setField = (field: keyof EmployerProfileInput, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const nextErrors = validateEmployerProfile(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    try {
      await updateProfile.mutateAsync(values);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể cập nhật hồ sơ", "error");
    }
  };

  const handleAvatar = async (file?: File) => {
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 5 * 1024 * 1024) {
      showToast("Ảnh đại diện phải là JPG hoặc PNG và không vượt quá 5 MB", "error");
      return;
    }
    try {
      await uploadAvatar.mutateAsync(file);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể tải ảnh đại diện", "error");
    }
  };

  return (
    <section aria-labelledby="profile-title">
      <div className="mb-6">
        <p className="text-label font-semibold text-gold">TÀI KHOẢN NHÀ TUYỂN DỤNG</p>
        <h1 id="profile-title" className="mt-1 text-headline text-navy">Hồ sơ cá nhân</h1>
        <p className="mt-2 text-ink-variant">Cập nhật thông tin người phụ trách tuyển dụng của công ty.</p>
      </div>

      <QueryBoundary
        isLoading={profileQuery.isLoading}
        error={profileQuery.error}
        onRetry={() => profileQuery.refetch()}
        skeleton={<SkeletonCard lines={6} className="max-w-3xl" />}
      >
        {profileQuery.data && (
          <Card className="max-w-3xl">
            <CardContent className="p-5 md:p-7">
              <div className="mb-8 flex flex-col gap-5 border-b border-border-subtle pb-7 sm:flex-row sm:items-center">
                {profileQuery.data.avatarUrl ? (
                  <img
                    src={profileQuery.data.avatarUrl}
                    alt={`Ảnh đại diện của ${profileQuery.data.fullName}`}
                    className="h-24 w-24 rounded-full border border-border-subtle object-cover"
                  />
                ) : (
                  <Avatar name={profileQuery.data.fullName} size="lg" className="h-24 w-24 text-headline" />
                )}
                <div>
                  <p className="font-semibold text-navy">Ảnh đại diện</p>
                  <p className="mt-1 text-label text-ink-muted">JPG hoặc PNG, tối đa 5 MB.</p>
                  <label className="mt-3 inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-default border border-navy px-4 py-2 text-label font-semibold text-navy transition-colors hover:bg-navy hover:text-white">
                    <IconCamera size={18} aria-hidden="true" />
                    {uploadAvatar.isPending ? "Đang tải..." : "Thay ảnh"}
                    <input
                      type="file"
                      className="sr-only"
                      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                      disabled={uploadAvatar.isPending}
                      onChange={(event) => void handleAvatar(event.target.files?.[0])}
                    />
                  </label>
                </div>
              </div>

              <form className="grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit} noValidate>
                <Field label="Họ và tên" htmlFor="employer-full-name" required error={errors.fullName} className="sm:col-span-2">
                  <Input id="employer-full-name" value={values.fullName} onChange={(event) => setField("fullName", event.target.value)} error={errors.fullName} />
                </Field>
                <Field label="Chức danh" htmlFor="employer-position" error={errors.position}>
                  <Input id="employer-position" value={values.position} onChange={(event) => setField("position", event.target.value)} error={errors.position} placeholder="Ví dụ: Quản lý tuyển dụng" />
                </Field>
                <Field label="Số điện thoại" htmlFor="employer-phone" error={errors.phone}>
                  <Input id="employer-phone" type="tel" value={values.phone} onChange={(event) => setField("phone", event.target.value)} error={errors.phone} placeholder="0912345678" />
                </Field>
                <Field label="Giới tính" htmlFor="employer-gender" error={errors.gender}>
                  <select
                    id="employer-gender"
                    value={values.gender}
                    onChange={(event) => setField("gender", event.target.value)}
                    className="h-11 rounded-default border border-border-strong bg-white px-3.5 text-ink focus:border-gold focus:ring-2 focus:ring-gold/20"
                  >
                    <option value="">Không cung cấp</option>
                    <option value="Male">Nam</option>
                    <option value="Female">Nữ</option>
                  </select>
                </Field>
                <div className="flex items-end sm:justify-end">
                  <Button type="submit" disabled={updateProfile.isPending} className="w-full sm:w-auto">
                    <IconId size={18} aria-hidden="true" />
                    {updateProfile.isPending ? "Đang lưu..." : "Lưu thay đổi"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </QueryBoundary>
    </section>
  );
}
