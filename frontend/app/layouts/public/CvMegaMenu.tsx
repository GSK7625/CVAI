/**
 * @file CvMegaMenu.tsx
 * @description Dropdown điều hướng công cụ tạo CV (Mẫu CV theo phong cách, theo ngành nghề, quản lý CV và cẩm nang viết CV).
 * @architecture Tuân thủ SRP & OCP: Độc lập logic menu Tạo CV và hiển thị dựa theo cấu hình.
 */

import { Link } from "react-router";

import {
  IconArrowRight,
  IconBox,
  IconCompass,
  IconStar,
  IconWriting,
  IconFileText,
  IconCloudUpload,
  IconFileDescription,
} from "@tabler/icons-react";
import {
  CV_STYLE_LINKS,
  CV_TOOL_LINKS,
} from "./navConfig";

interface CvMegaMenuProps {
  onClose: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

const CV_ICONS: Record<string, React.ReactNode> = {
  box: <IconBox size={18} className="text-gold" />,
  compass: <IconCompass size={18} className="text-gold" />,
  star: <IconStar size={18} className="text-gold" />,
  writing: <IconWriting size={18} className="text-gold" />,
  "file-text": <IconFileText size={19} className="text-gold" />,
  "cloud-upload": <IconCloudUpload size={19} className="text-gold" />,
  "file-description": <IconFileDescription size={19} className="text-gold" />,
};

export function CvMegaMenu({ onClose, onMouseEnter, onMouseLeave }: CvMegaMenuProps) {
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="absolute left-0 top-full z-50 w-[580px] rounded-2xl border border-border-subtle bg-white p-7 shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200"
    >
      <div className="grid grid-cols-12 gap-6 text-body-sm">
        {/* Cột 1: MẪU CV THEO STYLE & VỊ TRÍ (7 cols) */}
        <div className="col-span-7 border-r border-border-subtle pr-5">
          {/* Nhóm 1: Mẫu CV theo style */}
          <div className="mb-3">
            <Link
              to="/cv/templates"
              onClick={onClose}
              className="group inline-flex items-center gap-1 text-[13.5px] font-bold text-gold transition-colors hover:underline"
            >
              <span>Mẫu CV theo style</span>
              <IconArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
          <ul className="flex flex-col gap-2.5">
            {CV_STYLE_LINKS.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  onClick={onClose}
                  className="group flex items-center gap-2.5 font-medium text-ink hover:text-gold"
                >
                  {item.iconName && CV_ICONS[item.iconName]}
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Cột 2: QUẢN LÝ & CÔNG CỤ CV (5 cols) */}
        <div className="col-span-5 pl-2">
          <ul className="flex flex-col gap-3.5 pt-1">
            {CV_TOOL_LINKS.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  onClick={onClose}
                  className="group flex items-center gap-2.5 font-medium text-ink hover:text-gold"
                >
                  {item.iconName && CV_ICONS[item.iconName]}
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
