import Link from "next/link";

type DocPageProps = {
  title: string;
  children: React.ReactNode;
  nextHref?: string;
  nextLabel?: string;
  prevHref?: string;
  prevLabel?: string;
};

export function DocPage({ title, children, nextHref, nextLabel, prevHref, prevLabel }: DocPageProps) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 sm:px-8 lg:px-10">
      <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
        {title}
      </h1>
      <div className="docs-prose mt-8 text-white/80">
        {children}
      </div>
      {(prevHref || nextHref) && (
        <div className="mt-12 flex items-center justify-between border-t border-white/10 pt-8 text-sm text-white/50">
          <span>
            {prevHref && prevLabel && (
              <Link href={prevHref} className="font-medium text-brand-400 hover:underline">
                ← {prevLabel}
              </Link>
            )}
          </span>
          <span>
            {nextHref && nextLabel && (
              <Link href={nextHref} className="font-medium text-brand-400 hover:underline">
                {nextLabel} →
              </Link>
            )}
          </span>
        </div>
      )}
    </div>
  );
}
