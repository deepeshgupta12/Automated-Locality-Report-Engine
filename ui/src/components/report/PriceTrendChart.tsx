import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { priceTrend, narratives } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const PriceTrendChart = () => {
  const chartData = priceTrend.map((q: any) => ({
    quarter: q.quarterName,
    Locality: q.locationRate,
    "Micro-market": q.micromarketRate,
  }));

  const narrativeHtml = narratives?.page5_price_trend?.narrative || narratives?.["page5_price_trend.narrative"] || "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Asking Price Trend</h2>
      <p className="text-sm text-muted-foreground">Locality vs Micro-market (₹/sq ft)</p>

      {/* Step 5 Narratives (HTML) */}
      {narrativeHtml ? <NarrativeBlock html={narrativeHtml} /> : null}

      <div className="rounded-xl bg-card p-6 sy-card-shadow">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
            <XAxis dataKey="quarter" tick={{ fontSize: 12, fill: "hsl(220 10% 46%)" }} />
            <YAxis tick={{ fontSize: 12, fill: "hsl(220 10% 46%)" }} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{
                borderRadius: "0.75rem",
                border: "1px solid hsl(220 13% 91%)",
                boxShadow: "0 4px 16px hsl(220 20% 14% / 0.08)",
              }}
              formatter={(value: number) => [`₹ ${value.toLocaleString()}`, undefined]}
            />
            <Legend />
            <Line type="monotone" dataKey="Locality" stroke="hsl(8 80% 55%)" strokeWidth={3} dot={{ r: 5 }} />
            <Line
              type="monotone"
              dataKey="Micro-market"
              stroke="hsl(24 95% 53%)"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default PriceTrendChart;
