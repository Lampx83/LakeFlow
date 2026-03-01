import { DocsSidebar } from "@/components/docs/DocsSidebar";

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-0 w-full">
      <DocsSidebar />
      <article className="min-w-0 flex-1 border-t border-white/10">
        {children}
      </article>
    </div>
  );
}
