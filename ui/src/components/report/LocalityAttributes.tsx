import { CheckCircle2, AlertCircle } from "lucide-react";
import { positiveAttributes, negativeAttributes } from "@/lib/reportData";

const LocalityAttributes = () => {
  return (
    <section className="space-y-4">
      <h2 className="sy-section-title text-foreground">Locality Highlights</h2>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card p-6 sy-card-shadow space-y-3">
          <h3 className="text-sm font-semibold text-sy-green flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" /> What's Great
          </h3>
          <ul className="space-y-2">
            {positiveAttributes.map((a: any) => (
              <li key={a.attributeId} className="flex items-start gap-2 text-sm text-foreground">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-sy-green shrink-0" />
                {a.attributeDesc}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl bg-card p-6 sy-card-shadow space-y-3">
          <h3 className="text-sm font-semibold text-sy-red flex items-center gap-2">
            <AlertCircle className="h-4 w-4" /> What Needs Improvement
          </h3>
          <ul className="space-y-2">
            {negativeAttributes.map((a: any) => (
              <li key={a.attributeId} className="flex items-start gap-2 text-sm text-foreground">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-sy-red shrink-0" />
                {a.attributeDesc}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
};

export default LocalityAttributes;
