/**
 * @file JobMegaMenu.tsx
 * @description Mega Dropdown hiển thị danh mục việc làm (theo vị trí, ngành nghề, công ty, việc làm đã lưu/ứng tuyển).
 * @architecture Tuân thủ SRP (Đóng gói menu Việc làm riêng biệt) & OCP (Nạp danh mục từ file cấu hình navConfig).
 */

import { Link } from "react-router";

import {
  IconSearch,
  IconBookmark,
  IconFileText,
  IconThumbUp,
  IconBuilding,
  IconSparkles,
} from "@tabler/icons-react";
import {
  JOB_MENU_ACTIONS,
  JOB_POSITION_LINKS,
  JOB_FIELD_LINKS,
} from "./navConfig";

interface JobMegaMenuProps {
  onClose: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  search: <IconSearch size={18} className="text-gold" />,
  bookmark: <IconBookmark size={18} className="text-gold" />,
  "file-text": <IconFileText size={18} className="text-gold" />,
  "thumb-up": <IconThumbUp size={18} className="text-gold" />,
  building: <IconBuilding size={18} className="text-gold" />,
  sparkles: <IconSparkles size={18} className="text-gold" />,
};

export function JobMegaMenu({ onClose, onMouseEnter, onMouseLeave }: JobMegaMenuProps) {
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="absolute left-0 top-full z-50 w-[940px] rounded-2xl border border-border-subtle bg-white p-7 shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200"
    >
      <div className="grid grid-cols-12 gap-6 text-body-sm">
        {/* Cột 1: VIỆC LÀM & CÔNG TY (3 cols) */}
        <div className="col-span-3 border-r border-border-subtle pr-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-wider text-ink-muted">
            Việc làm
          </div>
          <ul className="flex flex-col gap-2.5">
            {JOB_MENU_ACTIONS.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  onClick={onClose}
                  className="group flex items-center gap-2.5 font-semibold text-navy hover:text-gold"
                >
                  {item.iconName && ACTION_ICONS[item.iconName]}
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Cột 2: VIỆC LÀM THEO VỊ TRÍ (6 cols - 2 sub-columns) */}
        <div className="col-span-6 border-r border-border-subtle px-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-wider text-ink-muted">
            Việc làm theo vị trí
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2.5">
            {JOB_POSITION_LINKS.map((item) => (
              <Link
                key={item.label}
                to={item.href}
                onClick={onClose}
                className="text-[13.5px] font-medium text-ink hover:text-gold"
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Cột 3: VIỆC LÀM THEO LĨNH VỰC (3 cols) */}
        <div className="col-span-3 pl-2">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-wider text-ink-muted">
            Việc làm theo lĩnh vực
          </div>
          <ul className="flex flex-col gap-2.5">
            {JOB_FIELD_LINKS.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  onClick={onClose}
                  className="text-[13.5px] font-medium text-ink hover:text-gold"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
