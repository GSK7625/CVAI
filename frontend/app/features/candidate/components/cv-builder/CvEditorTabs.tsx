/**
 * @file CvEditorTabs.tsx
 * @description Thanh điều hướng chuyển đổi giữa các tab nhập liệu của CV (Cá nhân, Kinh nghiệm, Học vấn, Kỹ năng).
 * @architecture Tuân thủ SRP: Chỉ quản lý việc hiển thị tab và emit sự kiện chuyển tab.
 */

export type CvTabKey = "info" | "experience" | "education" | "skills";


interface CvEditorTabsProps {
  activeTab: CvTabKey;
  onTabChange: (tab: CvTabKey) => void;
}

const TABS: { key: CvTabKey; label: string }[] = [
  { key: "info", label: "Cá nhân" },
  { key: "experience", label: "Kinh nghiệm" },
  { key: "education", label: "Học vấn" },
  { key: "skills", label: "Kỹ năng" },
];

export function CvEditorTabs({ activeTab, onTabChange }: CvEditorTabsProps) {
  return (
    <div className="flex rounded-xl border border-border-subtle bg-white p-1.5 shadow-sm">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onTabChange(tab.key)}
          className={`flex-1 rounded-lg py-2 text-center text-label-sm font-bold transition-all ${
            activeTab === tab.key
              ? "bg-navy text-white shadow-sm"
              : "text-ink hover:text-navy"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
