import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "LakeFlow — Data Lake pipelines for RAG & AI",
  description:
    "Ingest, process, embed, and semantic search. Python platform for Data Lake, Vector DB, and RAG. Open source, self-hosted.",
  openGraph: {
    title: "LakeFlow — Data Lake pipelines for RAG & AI",
    description:
      "Ingest, process, embed, and semantic search. Python platform for RAG & AI. Open source.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
