import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { propertyTypes, propertyStatus, narratives } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const toNum = (v: any) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

const PropertyRates = () => {
  // Payload keys:
  // propertyTypes: { propertyType, avgPrice, changePercent }
  // propertyStatus: { status, units, avgPrice, changePercent }

  const typeData = (Array.isArray(propertyTypes) ? propertyTypes : [])
    .map((p: any) => ({
      name: p.propertyType ?? p.type ?? p.name ?? "—",
      rate: toNum(p.avgPrice ?? p.avgRate ?? p.rate),
    }))
    .filter((d) => d.name !== "—" && d.rate > 0);

  const statusData = (Array.isArray(propertyStatus) ? propertyStatus : [])
    .map((p: any) => ({
      name: p.status ?? p.name ?? "—",
      rate: toNum(p.avgPrice ?? p.avgRate ?? p.rate),
    }))
    .filter((d) => d.name !== "—" && d.rate > 0);

  const narrativeHtml =
    narratives?.page9_propertytype_status?.narrative ||
    narratives?.["page9_propertytype_status.narrative"] ||
    "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Rates by Property Type & Project Status</h2>

      {/* Step 5 Narrative (HTML) */}
      <NarrativeBlock html={narrativeHtml} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card p-6 sy-card-shadow">
          <p className="text-sm font-semibold text-foreground mb-3">Property Type</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} />
              <Tooltip formatter={(value: number) => [`₹ ${Number(value).toLocaleString()}`, "Avg Rate"]} />
              <Bar dataKey="rate" radius={[6, 6, 0, 0]} fill="hsl(24 95% 53%)" />
            </BarChart>
          </ResponsiveContainer>

          {!typeData.length && (
            <p className="text-xs text-muted-foreground mt-3">Data not available for property types.</p>
          )}
        </div>

        <div className="rounded-xl bg-card p-6 sy-card-shadow">
          <p className="text-sm font-semibold text-foreground mb-3">Project Status</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={statusData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 91%)" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(220 10% 46%)" }} />
              <Tooltip formatter={(value: number) => [`₹ ${Number(value).toLocaleString()}`, "Avg Rate"]} />
              <Bar dataKey="rate" radius={[6, 6, 0, 0]} fill="hsl(220 14% 82%)" />
            </BarChart>
          </ResponsiveContainer>

          {!statusData.length && (
            <p className="text-xs text-muted-foreground mt-3">Data not available for project status.</p>
          )}
        </div>
      </div>
    </section>
  );
};

export default PropertyRates;