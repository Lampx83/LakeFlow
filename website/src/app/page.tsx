import { Hero } from "@/components/Hero";
import { ProductSection } from "@/components/ProductSection";
import { SolutionsSection } from "@/components/SolutionsSection";
import { DevelopersSection } from "@/components/DevelopersSection";
import { CtaSection } from "@/components/CtaSection";

export default function Home() {
  return (
    <>
      <Hero />
      <ProductSection />
      <SolutionsSection />
      <DevelopersSection />
      <CtaSection />
    </>
  );
}
