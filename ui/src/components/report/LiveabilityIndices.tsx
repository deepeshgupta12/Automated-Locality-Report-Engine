import { Train, ShoppingBag, GraduationCap, TreePine } from "lucide-react";
import { indices, localityName, cityName, micromarket, narratives } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const indexCards = [
  { label: "Connectivity", value: indices.connectivity_index, icon: Train, html: indices.connectivity_text, color: "sy-blue" },
  { label: "Lifestyle", value: indices.lifestyle_index, icon: ShoppingBag, html: indices.lifestyle_text, color: "sy-purple" },
  { label: "Education & Health", value: indices.educationhealth_index, icon: GraduationCap, html: indices.educationhealth_text, color: "sy-green" },
  { label: "Livability", value: indices.livability_index, icon: TreePine, html: indices.livability_text, color: "sy-amber" },
];

const ScoreRing = ({ value, color }: { value: number; color: string }) => {
  const percent = (value / 5) * 100;
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" fill="none" stroke="hsl(220 13% 91%)" strokeWidth="6" />
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          stroke={`hsl(var(--${color}))`}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <span className="absolute text-xl font-display font-bold text-foreground">{value.toFixed(1)}</span>
    </div>
  );
};

const LiveabilityIndices = () => {
  const summaryHtml = narratives?.page3_liveability?.summary || narratives?.["page3_liveability.summary"] || "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Liveability Indices</h2>
      <p className="text-sm text-muted-foreground">
        {localityName} · {cityName} · {micromarket}
      </p>

      {/* Step 5 Narratives (HTML) */}
      {summaryHtml ? (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Summary</h3>
          <NarrativeBlock html={summaryHtml} />
        </div>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {indexCards.map((card) => (
          <div key={card.label} className="rounded-xl bg-card p-5 sy-card-shadow text-center space-y-3">
            <div className="flex justify-center">
              <ScoreRing value={card.value} color={card.color} />
            </div>
            <div className="flex items-center justify-center gap-2">
              <card.icon className={`h-4 w-4 text-${card.color}`} />
              <span className="text-sm font-semibold text-foreground">{card.label}</span>
            </div>
            <div
              className="text-xs text-muted-foreground text-left [&_ul]:list-disc [&_ul]:pl-4 [&_li]:mb-1"
              dangerouslySetInnerHTML={{ __html: card.html }}
            />
          </div>
        ))}
      </div>
    </section>
  );
};

export default LiveabilityIndices;
