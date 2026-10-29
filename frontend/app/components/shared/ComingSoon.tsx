import { IconSettings } from "@tabler/icons-react";

/** Placeholder: khu HR đang được phát triển. */
export function ComingSoon({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-default border border-dashed border-border-strong bg-surface px-6 py-20 text-center">
      <IconSettings size={44} stroke={1.3} className="text-ink-muted" />
      <h1 className="mt-4 text-headline-md text-navy">{title}</h1>
      <p className="mt-2 text-ink-variant">Chức năng đang được phát triển và sẽ ra mắt sớm.</p>
    </div>
  );
}
