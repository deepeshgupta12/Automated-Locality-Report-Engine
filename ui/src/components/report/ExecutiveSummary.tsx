import { TrendingUp, Home, Star, FileText } from "lucide-react";
import {
  askingPrice,
  registrationRate,
  avgRating,
  reviewCount,
  totalProjects,
  saleCount,
  rentCount,
  narratives,
} from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const formatCurrency = (val: number) => `₹ ${(val / 1000).toFixed(1)}K`;

const stats = [
  {
    label: "Asking Price",
    sublabel: "per sq ft",
    value: formatCurrency(askingPrice),
    icon: TrendingUp,
    color: "bg-sy-orange-light text-sy-orange",
  },
  {
    label: "Registration Rate",
    sublabel: "per sq ft",
    value: formatCurrency(registrationRate),
    icon: FileText,
    color: "bg-sy-blue-light text-sy-blue",
  },
  {
    label: "Locality Rating",
    sublabel: `${reviewCount} Reviews`,
    value: avgRating.toFixed(1),
    icon: Star,
    color: "bg-sy-amber-light text-sy-amber",
  },
  {
    label: "Total Projects",
    sublabel: `${saleCount} Sale · ${rentCount} Rent`,
    value: totalProjects.toLocaleString(),
    icon: Home,
    color: "bg-sy-green-light text-sy-green",
  },
];

const ExecutiveSummary = () => {
  const takeawaysHtml =
    narratives?.page2_exec_snapshot?.takeaways ||
    narratives?.["page2_exec_snapshot.takeaways"] ||
    "";

  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Executive Summary</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl bg-card p-5 sy-card-shadow transition-all hover:sy-card-shadow-lg"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className={`rounded-lg p-2 ${stat.color}`}>
                <stat.icon className="h-4 w-4" />
              </div>
            </div>
            <p className="text-xl md:text-3xl font-display font-bold text-foreground">{stat.value}</p>
            <p className="text-sm font-medium text-foreground mt-1">{stat.label}</p>
            <p className="text-xs text-muted-foreground">{stat.sublabel}</p>
          </div>
        ))}
      </div>

      {/* Step 5 Narratives (HTML) */}
      {takeawaysHtml ? (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Key Takeaways</h3>
          <NarrativeBlock html={takeawaysHtml} />
        </div>
      ) : null}
    </section>
  );
};

export default ExecutiveSummary;
