/**
 * @file SkillsForm.tsx
 * @description Form quản lý danh sách kỹ năng chuyên môn dạng thẻ (Thêm nhanh kỹ năng bằng phím Enter, xóa thẻ kỹ năng).
 * @architecture Tuân thủ SRP (Chỉ quản lý danh sách kỹ năng) & ISP (Chỉ nhận mảng skills và handlers tương ứng).
 */

import { useState } from "react";


interface SkillsFormProps {
  skills: string[];
  onAddSkill: (skill: string) => void;
  onRemoveSkill: (index: number) => void;
}

export function SkillsForm({ skills, onAddSkill, onRemoveSkill }: SkillsFormProps) {
  const [newSkill, setNewSkill] = useState("");

  const handleAdd = () => {
    if (newSkill.trim()) {
      onAddSkill(newSkill.trim());
      setNewSkill("");
    }
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-subtle bg-white p-6 shadow-sm">
      <h3 className="border-b border-border-subtle pb-3 text-label font-bold text-navy">
        Kỹ năng chuyên môn
      </h3>

      <div className="flex items-center gap-2">
        <input
          type="text"
          value={newSkill}
          onChange={(e) => setNewSkill(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="Nhập kỹ năng mới rồi ấn Thêm..."
          className="flex-1 rounded-xl border border-border-subtle px-3.5 py-2 text-body text-ink outline-none focus:border-navy"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="rounded-xl bg-navy px-4 py-2 text-label font-bold text-white transition-all hover:bg-navy-secondary"
        >
          Thêm
        </button>
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        {skills.map((skill, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-low px-3 py-1.5 text-label-sm font-semibold text-navy"
          >
            <span>{skill}</span>
            <button
              type="button"
              onClick={() => onRemoveSkill(index)}
              className="text-ink-muted hover:text-danger"
              title="Xóa kỹ năng"
            >
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
