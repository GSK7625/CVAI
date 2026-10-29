/**
 * @file PersonalInfoForm.tsx
 * @description Form nhập và cập nhật thông tin cá nhân của ứng viên với Local Draft State + Debounce commit để tối ưu render.
 */

import { useEffect, useState } from "react";
import type { CvPersonalInfo } from "~/stores/useCvStore";

interface PersonalInfoFormProps {
  personalInfo: CvPersonalInfo;
  onUpdate: (data: Partial<CvPersonalInfo>) => void;
}

export function PersonalInfoForm({ personalInfo, onUpdate }: PersonalInfoFormProps) {
  const [draft, setDraft] = useState<CvPersonalInfo>(personalInfo);

  // Sync từ bên ngoài vào khi template được reset hoặc khởi tạo
  useEffect(() => {
    setDraft(personalInfo);
  }, [personalInfo]);

  // Debounce commit 300ms lên store
  useEffect(() => {
    if (draft === personalInfo) return;
    const t = window.setTimeout(() => {
      onUpdate(draft);
    }, 300);
    return () => window.clearTimeout(t);
  }, [draft, onUpdate, personalInfo]);

  const bind = (key: keyof CvPersonalInfo) => ({
    value: draft[key] ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setDraft((d) => ({ ...d, [key]: e.target.value })),
  });

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-subtle bg-white p-6 shadow-sm">
      <h3 className="border-b border-border-subtle pb-3 text-label font-bold text-navy">
        Thông tin cá nhân & Mục tiêu
      </h3>

      <div>
        <label className="mb-1 block text-label-sm font-semibold text-ink">Họ và tên</label>
        <input
          type="text"
          {...bind("fullName")}
          className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          placeholder="VD: Lê Quang Dũng"
        />
      </div>

      <div>
        <label className="mb-1 block text-label-sm font-semibold text-ink">Vị trí ứng tuyển</label>
        <input
          type="text"
          {...bind("title")}
          className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          placeholder="VD: Business Development Manager"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-label-sm font-semibold text-ink">Email</label>
          <input
            type="email"
            {...bind("email")}
            className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-label-sm font-semibold text-ink">Số điện thoại</label>
          <input
            type="text"
            {...bind("phone")}
            className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-label-sm font-semibold text-ink">Địa chỉ / Khu vực</label>
          <input
            type="text"
            {...bind("location")}
            className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-label-sm font-semibold text-ink">Website / LinkedIn</label>
          <input
            type="text"
            {...bind("website")}
            className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-label-sm font-semibold text-ink">Ảnh đại diện (URL)</label>
        <input
          type="text"
          {...bind("avatar")}
          className="w-full rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          placeholder="Link ảnh chân dung..."
        />
      </div>

      <div>
        <label className="mb-1 block text-label-sm font-semibold text-ink">Mục tiêu nghề nghiệp</label>
        <textarea
          rows={4}
          {...bind("summary")}
          className="w-full rounded-xl border border-border-subtle px-3.5 py-2.5 text-body text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          placeholder="Tóm tắt kinh nghiệm và định hướng phát triển..."
        />
      </div>
    </div>
  );
}
