/**
 * @file JobSearchBar.tsx
 * @description Khung tìm kiếm việc làm độc lập (từ khóa + địa điểm + nút tìm kiếm).
 * @architecture Uncontrolled/Local-state cho từ khóa tới khi submit; chọn địa điểm kích hoạt submit ngay.
 */

import { useState, useEffect, memo, type FormEvent } from "react";
import { IconSearch, IconMapPin } from "@tabler/icons-react";
import { Button } from "~/components/ui/Button";
import type { LookupOption } from "../../types";

export interface JobSearchBarProps {
  keyword: string;
  locationId?: string;
  locations?: LookupOption[];
  loadingLocations?: boolean;
  className?: string;
  onSubmit: (v: { keyword: string; locationId?: string }) => void;
}

export const JobSearchBar = memo(function JobSearchBar({
  keyword,
  locationId,
  locations = [],
  loadingLocations = false,
  className = "",
  onSubmit,
}: JobSearchBarProps) {
  const [localKeyword, setLocalKeyword] = useState(keyword);
  const [localLocationId, setLocalLocationId] = useState(locationId ?? "");

  useEffect(() => {
    setLocalKeyword(keyword);
  }, [keyword]);

  useEffect(() => {
    setLocalLocationId(locationId ?? "");
  }, [locationId]);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    onSubmit({
      keyword: localKeyword.trim(),
      locationId: localLocationId || undefined,
    });
  };

  const handleLocationChange = (newLocId: string) => {
    setLocalLocationId(newLocId);
    onSubmit({
      keyword: localKeyword.trim(),
      locationId: newLocId || undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex w-full flex-col gap-3 rounded-xl bg-white p-3 shadow-overlay md:flex-row md:items-center ${className}`}
    >
      <div className="flex flex-grow items-center rounded-default border border-border-strong bg-surface-low px-4 transition-all focus-within:border-gold focus-within:bg-white focus-within:ring-2 focus-within:ring-gold/20">
        <IconSearch size={20} stroke={1.6} className="mr-3 shrink-0 text-ink-muted" />
        <input
          type="text"
          value={localKeyword}
          onChange={(e) => setLocalKeyword(e.target.value)}
          placeholder="Tìm kiếm việc làm, công ty..."
          className="w-full border-none bg-transparent py-3 text-body text-ink outline-none ring-0 placeholder:text-ink-muted/70 focus:outline-none focus:ring-0"
          aria-label="Từ khóa tìm kiếm"
        />
      </div>

      <div className="flex items-center rounded-default border border-border-strong bg-surface-low px-4 transition-all focus-within:border-gold focus-within:bg-white focus-within:ring-2 focus-within:ring-gold/20 md:w-56">
        <IconMapPin size={20} stroke={1.6} className="mr-3 shrink-0 text-ink-muted" />
        <select
          value={localLocationId}
          onChange={(e) => handleLocationChange(e.target.value)}
          disabled={loadingLocations}
          className="w-full cursor-pointer border-none bg-transparent py-3 text-body text-ink outline-none ring-0 focus:outline-none focus:ring-0 disabled:opacity-60"
          aria-label="Địa điểm"
        >
          <option value="">Tất cả địa điểm</option>
          {locations && locations.length > 0
            ? locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))
            : null}
        </select>
      </div>

      <Button
        type="submit"
        variant="accent"
        size="lg"
        className="shrink-0 font-semibold md:px-8"
      >
        Tìm kiếm
      </Button>
    </form>
  );
});
