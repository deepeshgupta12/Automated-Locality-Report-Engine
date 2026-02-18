import { TrendingUp, TrendingDown } from "lucide-react";
import { topProjectsByTxn, narratives } from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const TopProjects = () => {
  const projects = topProjectsByTxn.slice(0, 10);

  const highlightsHtml =
    narratives?.page10_top_projects?.highlights || narratives?.["page10_top_projects.highlights"] || "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Top Projects by Transactions</h2>

      {/* Step 5 Narrative (HTML) */}
      <NarrativeBlock html={highlightsHtml} />

      <div className="rounded-xl bg-card sy-card-shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="sy-gradient">
                <th className="text-left py-3 px-4 text-xs font-semibold text-primary-foreground">#</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-primary-foreground">Project</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-primary-foreground">Locality</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-primary-foreground">Txns</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-primary-foreground">Rate (₹/sqft)</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-primary-foreground">Change</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p: any, i: number) => (
                <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-secondary/30">
                  <td className="py-3 px-4 font-medium text-muted-foreground">{i + 1}</td>
                  <td className="py-3 px-4 font-semibold text-foreground">{p.projectName}</td>
                  <td className="py-3 px-4 text-muted-foreground">{p.locality}</td>
                  <td className="text-right py-3 px-4 font-semibold text-foreground">{p.noOfTransactions}</td>
                  <td className="text-right py-3 px-4 text-foreground">₹ {p.currentRate.toLocaleString()}</td>
                  <td className="text-right py-3 px-4">
                    {p.changePercentage != null ? (
                      <span
                        className={`inline-flex items-center gap-1 text-xs font-semibold ${
                          p.changePercentage >= 0 ? "text-sy-green" : "text-sy-red"
                        }`}
                      >
                        {p.changePercentage >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        {p.changePercentage >= 0 ? "+" : ""}
                        {p.changePercentage.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};

export default TopProjects;
