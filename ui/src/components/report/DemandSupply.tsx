import { demandSupplySale, demandSupplyRent, narratives } from "@/lib/reportData";

const escapeHtml = (s: string) =>
  s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const toHtml = (maybeHtml: any) => {
  if (typeof maybeHtml !== "string") return "";
  const t = maybeHtml.trim();
  if (!t) return "";
  // If it already looks like HTML, keep it. Else wrap safely in <p>
  const looksLikeHtml = /<\/?[a-z][\s\S]*>/i.test(t);
  return looksLikeHtml ? t : `<p>${escapeHtml(t)}</p>`;
};

const DemandSupplyNarrative = () => {
  const buyRaw =
    narratives?.page7_demand_supply_sale?.narrative || narratives?.["page7_demand_supply_sale.narrative"] || "";
  const rentRaw =
    narratives?.page8_demand_supply_rent?.narrative || narratives?.["page8_demand_supply_rent.narrative"] || "";

  const buyHtml = toHtml(buyRaw);
  const rentHtml = toHtml(rentRaw);

  if (!buyHtml && !rentHtml) return null;

  return (
    <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {buyHtml ? (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-foreground">Buy summary</h3>
            <div
              className="text-sm text-muted-foreground text-left [&_ul]:list-disc [&_ul]:pl-5 [&_li]:mb-1 [&_p]:mb-2"
              dangerouslySetInnerHTML={{ __html: buyHtml }}
            />
          </div>
        ) : null}

        {rentHtml ? (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-foreground">Rent summary</h3>
            <div
              className="text-sm text-muted-foreground text-left [&_ul]:list-disc [&_ul]:pl-5 [&_li]:mb-1 [&_p]:mb-2"
              dangerouslySetInnerHTML={{ __html: rentHtml }}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
};

const DemandSupplyTable = ({ title, data, type }: { title: string; data: any[]; type: string }) => {
  const safe = Array.isArray(data) ? data : [];
  const filtered = safe.filter((d: any) => (d?.demandPercent ?? 0) > 0 || (d?.supplyPercent ?? 0) > 2);

  return (
    <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-3">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">{type}</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Demand%</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Supply%</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Gap</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row: any) => {
              const gap = (row?.demandPercent ?? 0) - (row?.supplyPercent ?? 0);
              return (
                <tr key={row.name} className="border-b border-border/50 last:border-0">
                  <td className="py-2 px-3 font-medium text-foreground">{row.name}</td>
                  <td className="text-right py-2 px-3 text-muted-foreground">{row.demandPercent}%</td>
                  <td className="text-right py-2 px-3 text-muted-foreground">{row.supplyPercent}%</td>
                  <td
                    className={`text-right py-2 px-3 font-semibold ${
                      gap > 0 ? "text-sy-green" : gap < 0 ? "text-sy-red" : "text-muted-foreground"
                    }`}
                  >
                    {gap > 0 ? "+" : ""}
                    {gap}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const DemandSupply = () => {
  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Demand vs Supply Segmentation</h2>

      {/* Step 5 Narratives (HTML) */}
      <DemandSupplyNarrative />

      <div className="space-y-6">
        <div>
          <h3 className="text-base font-semibold text-foreground mb-3">Buy</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <DemandSupplyTable title="By Unit Type" data={demandSupplySale?.unitType} type="Unit" />
            <DemandSupplyTable title="By Property Type" data={demandSupplySale?.propertyType} type="Property" />
            <DemandSupplyTable title="By Price Band" data={demandSupplySale?.totalPrice_range} type="Range" />
          </div>
        </div>

        <div>
          <h3 className="text-base font-semibold text-foreground mb-3">Rent</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <DemandSupplyTable title="By Unit Type" data={demandSupplyRent?.unitType} type="Unit" />
            <DemandSupplyTable title="By Property Type" data={demandSupplyRent?.propertyType} type="Property" />
            <DemandSupplyTable title="By Price Band" data={demandSupplyRent?.totalPrice_range} type="Range" />
          </div>
        </div>
      </div>
    </section>
  );
};

export default DemandSupply;