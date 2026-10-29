/**
 * @file CvCockpitSkeleton.tsx
 * @description Skeleton loader mô phỏng bố cục Candidate Career & CV Cockpit.
 * Design: Midnight & Gold, @tabler/icons-react.
 */

import { Skeleton } from "~/components/ui";

export function CvCockpitSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Metric cards skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="p-5 rounded-2xl border border-border-subtle bg-surface space-y-3"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24 rounded-md" />
              <Skeleton className="w-8 h-8 rounded-xl" />
            </div>
            <Skeleton className="h-7 w-16 rounded-md" />
            <Skeleton className="h-3 w-36 rounded-md" />
          </div>
        ))}
      </div>

      {/* Main content split skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-4">
          <Skeleton className="h-12 w-full rounded-2xl" />
          {Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="p-1 rounded-[1.75rem] bg-navy/5 border border-navy/10"
            >
              <div className="p-6 bg-white rounded-[calc(1.75rem-0.25rem)] space-y-4">
                <div className="flex items-start gap-4">
                  <Skeleton className="w-16 h-20 rounded-xl shrink-0" />
                  <div className="flex-1 space-y-2.5">
                    <Skeleton className="h-5 w-48 rounded-md" />
                    <Skeleton className="h-3.5 w-32 rounded-md" />
                    <Skeleton className="h-5 w-20 rounded-full" />
                  </div>
                </div>
                <div className="flex gap-2 pt-3 border-t border-border-subtle">
                  <Skeleton className="h-8 w-36 rounded-xl" />
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="lg:col-span-4 space-y-6">
          <Skeleton className="h-64 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
        </div>
      </div>
    </div>
  );
}
