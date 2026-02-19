import { FileText, TrendingUp } from "lucide-react";
import { govtRegistration, topDevelopersByTxn, narratives } from "@/lib/reportData";

const RegistrationOverview = () => {
  const txn =
    (govtRegistration as any)?.transactionCount ??
    (govtRegistration as any)?.totalTransactions ??
    null;

  const gross =
    (govtRegistration as any)?.grossValue ??
    (govtRegistration as any)?.totalValue ??
    null;

  const period =
    (govtRegistration as any)?.dateRange ??
    (govtRegistration as any)?.period ??
    "";

  const rate =
    (govtRegistration as any)?.registeredRate ??
    (govtRegistration as any)?.avgRegisteredRate ??
    null;

  const devs = Array.isArray(topDevelopersByTxn) ? topDevelopersByTxn : [];
  const topDevs = devs.slice(0, 10);

  const narrativeHtml =
    narratives?.page11_registrations_developers?.narrative || "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Registrations & Developers</h2>

      {narrativeHtml ? (
        <div
          className="rounded-xl bg-card p-5 sy-card-shadow text-sm text-muted-foreground
                     [&_ul]:list-disc [&_ul]:pl-5 [&_li]:mb-1"
          dangerouslySetInnerHTML={{ __html: narrativeHtml }}
        />
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-card p-5 sy-card-shadow">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-sy-blue" />
            <p className="text-sm font-semibold text-foreground">Govt Transactions</p>
          </div>
          <p className="text-2xl font-display font-bold text-foreground">
            {txn ?? "—"}
          </p>
          <p className="text-xs text-muted-foreground">{period || "—"}</p>
        </div>

        <div className="rounded-xl bg-card p-5 sy-card-shadow">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-sy-green" />
            <p className="text-sm font-semibold text-foreground">Gross Value</p>
          </div>
          <p className="text-2xl font-display font-bold text-foreground">
            {gross ?? "—"}
          </p>
          <p className="text-xs text-muted-foreground">As per registrations</p>
        </div>

        <div className="rounded-xl bg-card p-5 sy-card-shadow">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-sy-amber" />
            <p className="text-sm font-semibold text-foreground">Registered Rate</p>
          </div>
          <p className="text-2xl font-display font-bold text-foreground">
            {rate != null ? `₹ ${Number(rate).toLocaleString()}` : "—"}
          </p>
          <p className="text-xs text-muted-foreground">Avg registered ₹/sq ft</p>
        </div>
      </div>

      <div className="rounded-xl bg-card sy-card-shadow overflow-hidden">
        <div className="px-5 pt-5">
          <h3 className="text-sm font-semibold text-foreground">Top Developers by Transactions</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Based on government transaction records.
          </p>
        </div>

        <div className="overflow-x-auto mt-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-t border-border bg-secondary/40">
                <th className="text-left py-3 px-5 text-xs font-semibold text-muted-foreground">#</th>
                <th className="text-left py-3 px-5 text-xs font-semibold text-muted-foreground">Developer</th>
                <th className="text-right py-3 px-5 text-xs font-semibold text-muted-foreground">Txns</th>
              </tr>
            </thead>
            <tbody>
              {topDevs.length > 0 ? (
                topDevs.map((d: any, i: number) => (
                  <tr key={i} className="border-t border-border/60 hover:bg-secondary/20">
                    <td className="py-3 px-5 text-muted-foreground">{i + 1}</td>
                    <td className="py-3 px-5 font-medium text-foreground">
                      {d.developerName ?? d.name ?? "—"}
                    </td>
                    <td className="py-3 px-5 text-right font-semibold text-foreground">
                      {d.noOfTransactions ?? d.transactions ?? "—"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="py-4 px-5 text-sm text-muted-foreground" colSpan={3}>
                    Developer transaction data not available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};

export default RegistrationOverview;