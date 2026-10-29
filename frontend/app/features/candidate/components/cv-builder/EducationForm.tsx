/**
 * @file EducationForm.tsx
 * @description Form quản lý danh sách học vấn và bằng cấp (Thêm mới, sửa đổi trường học/chuyên ngành/GPA, xóa mục học vấn).
 * @architecture Tuân thủ SRP (Chỉ quản lý danh sách học vấn) & ISP (Chỉ nhận mảng educations và các handler tương ứng).
 */

import { IconPlus, IconTrash } from "@tabler/icons-react";

import type { CvEducation } from "~/stores/useCvStore";

interface EducationFormProps {
  educations: CvEducation[];
  onAdd: () => void;
  onUpdate: (id: string, data: Partial<CvEducation>) => void;
  onRemove: (id: string) => void;
}

export function EducationForm({
  educations,
  onAdd,
  onUpdate,
  onRemove,
}: EducationFormProps) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-subtle bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <h3 className="text-label font-bold text-navy">Học vấn & Bằng cấp</h3>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1 text-label-sm font-bold text-gold hover:underline"
        >
          <IconPlus size={16} /> Thêm học vấn
        </button>
      </div>

      <div className="flex flex-col gap-5">
        {educations.map((edu, index) => (
          <div
            key={edu.id}
            className="relative flex flex-col gap-3 rounded-xl border border-border-subtle bg-slate-50/70 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-bold text-navy">
                Học vấn #{index + 1}
              </span>
              {educations.length > 1 && (
                <button
                  type="button"
                  onClick={() => onRemove(edu.id)}
                  className="text-danger hover:opacity-80"
                  title="Xóa"
                >
                  <IconTrash size={16} />
                </button>
              )}
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-ink">
                Chuyên ngành / Bằng cấp
              </label>
              <input
                type="text"
                value={edu.degree}
                onChange={(e) => onUpdate(edu.id, { degree: e.target.value })}
                className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
              />
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-ink">
                Trường Đào tạo
              </label>
              <input
                type="text"
                value={edu.school}
                onChange={(e) => onUpdate(edu.id, { school: e.target.value })}
                className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Bắt đầu
                </label>
                <input
                  type="text"
                  value={edu.startDate}
                  onChange={(e) => onUpdate(edu.id, { startDate: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Kết thúc
                </label>
                <input
                  type="text"
                  value={edu.endDate}
                  onChange={(e) => onUpdate(edu.id, { endDate: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-ink">
                Xếp loại / GPA
              </label>
              <input
                type="text"
                value={edu.gpa}
                onChange={(e) => onUpdate(edu.id, { gpa: e.target.value })}
                className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
