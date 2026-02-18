import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { nearbyLocalities, localityName, askingPrice, narratives } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const NearbyLocalities = () => {
  const chartData = [
    { name: localityName, avgRate: askingPrice, change: 0, isSubject: true },
    ...nearbyLocalities.map((l: any) => ({
      name: l.name,
      avgRate: l.avgRate,
      change: l.changePercentage,
      isSubject: false,
    })),
  ].sort((a, b) => b.avgRate - a.avgRate);

  const narrativeHtml =
    narratives?.page6_nearby_comparison?.narrative || narratives?.["page6_nearby_comparison.narrative"] || "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Locality vs Nearby Localities</h2>
      <p className="text-sm text-muted-foreground">Average asking rate comparison (₹/sq ft)</p>

      {/* Step 5 Narratives (HTML) */}
      {narrativeHtml ? <NarrativeBlock html={narrativeHtml} /> : null}

      <div className="rounded-xl bg-card p-6 sy-card-shadow">
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`}
            />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} width={120} />
            <Tooltip formatter={(value: number) => [`₹ ${value.toLocaleString()}`, "Avg Rate"]} />
            <Bar dataKey="avgRate" radius={[0, 6, 6, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.isSubject ? "hsl(8 80% 55%)" : "hsl(220 14% 82%)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default NearbyLocalities;
