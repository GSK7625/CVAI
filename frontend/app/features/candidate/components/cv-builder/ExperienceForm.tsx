/**
 * @file ExperienceForm.tsx
 * @description Form quản lý danh sách kinh nghiệm làm việc (Thêm mới, sửa đổi thông tin công ty/vị trí/thời gian, xóa mục kinh nghiệm).
 * @architecture Tuân thủ SRP (Chỉ quản lý danh sách kinh nghiệm) & ISP (Chỉ nhận mảng experiences và các handler tương ứng).
 */

import { IconPlus, IconTrash } from "@tabler/icons-react";

import type { CvExperience } from "~/stores/useCvStore";

interface ExperienceFormProps {
  experiences: CvExperience[];
  onAdd: () => void;
  onUpdate: (id: string, data: Partial<CvExperience>) => void;
  onRemove: (id: string) => void;
}

export function ExperienceForm({
  experiences,
  onAdd,
  onUpdate,
  onRemove,
}: ExperienceFormProps) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-subtle bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <h3 className="text-label font-bold text-navy">Kinh nghiệm làm việc</h3>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1 text-label-sm font-bold text-gold hover:underline"
        >
          <IconPlus size={16} /> Thêm vị trí
        </button>
      </div>

      <div className="flex flex-col gap-5">
        {experiences.map((exp, index) => (
          <div
            key={exp.id}
            className="relative flex flex-col gap-3 rounded-xl border border-border-subtle bg-slate-50/70 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-bold text-navy">
                Kinh nghiệm #{index + 1}
              </span>
              {experiences.length > 1 && (
                <button
                  type="button"
                  onClick={() => onRemove(exp.id)}
                  className="text-danger hover:opacity-80"
                  title="Xóa"
                >
                  <IconTrash size={16} />
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Vị trí / Chức danh
                </label>
                <input
                  type="text"
                  value={exp.role}
                  onChange={(e) => onUpdate(exp.id, { role: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Tên công ty
                </label>
                <input
                  type="text"
                  value={exp.company}
                  onChange={(e) => onUpdate(exp.id, { company: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Bắt đầu
                </label>
                <input
                  type="text"
                  value={exp.startDate}
                  onChange={(e) => onUpdate(exp.id, { startDate: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-ink">
                  Kết thúc
                </label>
                <input
                  type="text"
                  value={exp.endDate}
                  onChange={(e) => onUpdate(exp.id, { endDate: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-white px-3 py-1.5 text-label-sm outline-none focus:border-navy"
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-ink">
                Mô tả công việc & Thành tích
              </label>
              <textarea
                rows={3}
                value={exp.description}
                onChange={(e) => onUpdate(exp.id, { description: e.target.value })}
                className="w-full rounded-lg border border-border-subtle bg-white px-3 py-2 text-label-sm outline-none focus:border-navy"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
