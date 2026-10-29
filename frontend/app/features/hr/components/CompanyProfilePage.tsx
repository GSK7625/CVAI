import { useEffect, useState, type FormEvent } from "react";
import { IconBuilding, IconPhoto, IconRosetteDiscountCheck } from "@tabler/icons-react";
import { Badge, Button, Card, CardContent, Field, Input } from "~/components/ui";
import { QueryBoundary, SkeletonCard } from "~/components/shared/QueryBoundary";
import { useUIStore } from "~/stores/useUIStore";
import { validateCompanyProfile, type FieldErrors } from "../contracts/hrContracts";
import {
  useCompanyProfile,
  useCreateCompany,
  useUpdateCompany,
  useUploadCompanyLogo,
} from "../hooks/useCompanyProfile";
import type { CompanyProfileInput } from "../types";

const emptyForm: CompanyProfileInput = {
  name: "",
  scale: "",
  industry: "",
  websiteUrl: "",
  address: "",
  description: "",
};

export function CompanyProfilePage() {
  const companyQuery = useCompanyProfile();
  const createCompany = useCreateCompany();
  const updateCompany = useUpdateCompany();
  const uploadLogo = useUploadCompanyLogo();
  const showToast = useUIStore((state) => state.showToast);
  const [values, setValues] = useState(emptyForm);
  const [errors, setErrors] = useState<FieldErrors<CompanyProfileInput>>({});

  useEffect(() => {
    if (!companyQuery.data) return;
    setValues({
      name: companyQuery.data.name,
      scale: companyQuery.data.scale ?? "",
      industry: companyQuery.data.industry ?? "",
      websiteUrl: companyQuery.data.websiteUrl ?? "",
      address: companyQuery.data.address ?? "",
      description: companyQuery.data.description ?? "",
    });
  }, [companyQuery.data]);

  const mode = companyQuery.data ? "update" : "create";
  const activeMutation = mode === "create" ? createCompany : updateCompany;
  const setField = (field: keyof CompanyProfileInput, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const nextErrors = validateCompanyProfile(values, mode);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    try {
      await activeMutation.mutateAsync(values);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể lưu hồ sơ công ty", "error");
    }
  };

  const handleLogo = async (file?: File) => {
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 5 * 1024 * 1024) {
      showToast("Logo phải là JPG hoặc PNG và không vượt quá 5 MB", "error");
      return;
    }
    try {
      await uploadLogo.mutateAsync(file);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể tải logo", "error");
    }
  };

  return (
    <section aria-labelledby="company-title">
      <div className="mb-6">
        <p className="text-label font-semibold text-gold">THÔNG TIN DOANH NGHIỆP</p>
        <h1 id="company-title" className="mt-1 text-headline text-navy">Hồ sơ công ty</h1>
        <p className="mt-2 text-ink-variant">Thông tin này xuất hiện cùng các tin tuyển dụng của công ty.</p>
      </div>

      <QueryBoundary
        isLoading={companyQuery.isLoading}
        error={companyQuery.error}
        onRetry={() => companyQuery.refetch()}
        skeleton={<SkeletonCard lines={8} className="max-w-4xl" />}
      >
        <Card className="max-w-4xl">
          <CardContent className="p-5 md:p-7">
            <div className="mb-8 flex flex-col gap-5 border-b border-border-subtle pb-7 sm:flex-row sm:items-center">
              <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-default border border-border-subtle bg-surface-low">
                {companyQuery.data?.logoUrl ? (
                  <img src={companyQuery.data.logoUrl} alt={`Logo ${companyQuery.data.name}`} className="h-full w-full object-cover" />
                ) : (
                  <IconBuilding size={42} stroke={1.4} className="text-ink-muted" aria-hidden="true" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-navy">Logo công ty</p>
                  {companyQuery.data && (
                    <Badge variant={companyQuery.data.verifiedStatus === "Verified" ? "success" : "neutral"}>
                      <IconRosetteDiscountCheck size={14} aria-hidden="true" />
                      {companyQuery.data.verifiedStatus === "Verified" ? "Đã xác minh" : "Chưa xác minh"}
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-label text-ink-muted">JPG hoặc PNG, tối đa 5 MB.</p>
                {companyQuery.data && (
                  <label className="mt-3 inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-default border border-navy px-4 py-2 text-label font-semibold text-navy transition-colors hover:bg-navy hover:text-white">
                    <IconPhoto size={18} aria-hidden="true" />
                    {uploadLogo.isPending ? "Đang tải..." : "Thay logo"}
                    <input
                      type="file"
                      className="sr-only"
                      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                      disabled={uploadLogo.isPending}
                      onChange={(event) => void handleLogo(event.target.files?.[0])}
                    />
                  </label>
                )}
              </div>
            </div>

            {!companyQuery.data && (
              <div className="mb-6 rounded-default border border-gold/30 bg-gold/10 px-4 py-3 text-label text-ink-variant">
                Tài khoản chưa liên kết với công ty. Hoàn thành thông tin bên dưới để tạo hồ sơ công ty.
              </div>
            )}

            <form className="grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit} noValidate>
              <Field label="Tên công ty" htmlFor="company-name" required error={errors.name} className="sm:col-span-2">
                <Input id="company-name" value={values.name} onChange={(event) => setField("name", event.target.value)} error={errors.name} />
              </Field>
              <Field label="Ngành nghề" htmlFor="company-industry" error={errors.industry}>
                <Input id="company-industry" value={values.industry} onChange={(event) => setField("industry", event.target.value)} error={errors.industry} />
              </Field>
              <Field label="Quy mô" htmlFor="company-scale" error={errors.scale}>
                <Input id="company-scale" value={values.scale} onChange={(event) => setField("scale", event.target.value)} error={errors.scale} placeholder="Ví dụ: 50–100 nhân sự" />
              </Field>
              <Field label="Website" htmlFor="company-website" error={errors.websiteUrl} className="sm:col-span-2">
                <Input id="company-website" type="url" value={values.websiteUrl} onChange={(event) => setField("websiteUrl", event.target.value)} error={errors.websiteUrl} placeholder="https://example.com" />
              </Field>
              <Field label="Địa chỉ" htmlFor="company-address" className="sm:col-span-2">
                <Input id="company-address" value={values.address} onChange={(event) => setField("address", event.target.value)} />
              </Field>
              <Field label="Giới thiệu công ty" htmlFor="company-description" className="sm:col-span-2">
                <textarea
                  id="company-description"
                  rows={6}
                  value={values.description}
                  onChange={(event) => setField("description", event.target.value)}
                  className="rounded-default border border-border-strong bg-white px-3.5 py-3 text-ink focus:border-gold focus:ring-2 focus:ring-gold/20"
                />
              </Field>
              <div className="sm:col-span-2 sm:flex sm:justify-end">
                <Button type="submit" disabled={activeMutation.isPending} className="w-full sm:w-auto">
                  {activeMutation.isPending ? "Đang lưu..." : mode === "create" ? "Tạo hồ sơ công ty" : "Lưu thay đổi"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </QueryBoundary>
    </section>
  );
}
