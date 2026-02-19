import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { marketSupply, rentalStats, marketSnapshotNarrative } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const MarketSnapshot = () => {
  const supplyData = (marketSupply?.graphData || []).map((d: any) => ({
    bucket: d.bucketRange,
    Listings: d.saleCount,
  }));

  const parseRent = (str: string) => {
    const s = (str || "").toString();
    const cleaned = s.replace("₹", "").replace(/\s/g, "").replace("K", "").replace("L", "");
    if (s.includes("L")) return parseFloat(cleaned) * 100000;
    if (s.includes("K")) return parseFloat(cleaned) * 1000;
    const n = parseFloat(cleaned);
    return Number.isFinite(n) ? n : 0;
  };

  const rentData = Array.isArray(rentalStats)
    ? rentalStats.map((r: any) => ({
        type: r.unitType,
        Rent: parseRent(r.avgRate),
        display: r.avgRate,
      }))
    : [];

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Market Snapshot</h2>

      {/* Step 5 Narrative */}
      {marketSnapshotNarrative ? (
        <div className="rounded-xl bg-card p-5 sy-card-shadow text-sm text-muted-foreground">
          <NarrativeBlock html={marketSnapshotNarrative} />
        </div>
      ) : null}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card p-6 sy-card-shadow space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Buy: Supply Distribution (₹/sq ft)</h3>
          <p className="text-xs text-muted-foreground">{marketSupply?.description ?? ""}</p>

          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={supplyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: "hsl(220 10% 46%)" }} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} />
              <Tooltip />
              <Bar dataKey="Listings" fill="hsl(8 80% 55%)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl bg-card p-6 sy-card-shadow space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Rent: Avg Monthly Rent by Unit Type</h3>

          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={rentData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }}
                tickFormatter={(v) => `₹${(Number(v) / 1000).toFixed(0)}K`}
              />
              <YAxis
                dataKey="type"
                type="category"
                tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }}
                width={60}
              />
              <Tooltip formatter={(value: number) => [`₹ ${Number(value).toLocaleString()}`, "Avg Rent"]} />
              <Bar dataKey="Rent" fill="hsl(24 95% 53%)" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
};

export default MarketSnapshot;