import { Star, ThumbsUp, ThumbsDown, User } from "lucide-react";
import {
  topReviews,
  reviewGood,
  reviewBad,
  avgRating,
  reviewCount,
  ratingStarCount,
  narratives,
} from "@/lib/reportData";
import NarrativeBlock from "./NarrativeBlock";

const ReviewsSection = () => {
  const totalStars = ratingStarCount.reduce((sum: number, r: any) => sum + (r.Count || 0), 0);

  const conclusionHtml =
    narratives?.page12_reviews_conclusion?.conclusion || narratives?.["page12_reviews_conclusion.conclusion"] || "";

  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <h2 className="sy-section-title text-foreground">Ratings & Reviews</h2>
        <p className="text-sm text-muted-foreground">
          Community sentiment from available reviews in the source payload.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-2">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Star className="h-4 w-4" />
            Avg Rating
          </div>
          <p className="text-2xl font-display font-bold text-foreground">{avgRating} / 5</p>
          <p className="text-xs text-muted-foreground">{reviewCount?.toLocaleString?.() ?? "—"} reviews</p>
        </div>

        <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-2">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <User className="h-4 w-4" />
            Reviews Included
          </div>
          <p className="text-2xl font-display font-bold text-foreground">{reviewCount?.toLocaleString?.() ?? "—"}</p>
          <p className="text-xs text-muted-foreground">From current feed</p>
        </div>
      </div>

      {/* Star distribution */}
      <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Star Distribution</h3>
        <div className="space-y-3">
          {ratingStarCount
            .slice()
            .sort((a: any, b: any) => (b.Rating || 0) - (a.Rating || 0))
            .map((r: any) => {
              const pct = totalStars > 0 ? (r.Count / totalStars) * 100 : 0;
              return (
                <div key={r.Rating} className="flex items-center gap-3">
                  <div className="w-10 text-xs text-muted-foreground">{r.Rating}★</div>
                  <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
                    <div className="h-2 bg-primary" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="w-12 text-right text-xs text-muted-foreground">{r.Count ?? 0}</div>
                </div>
              );
            })}
          {(!ratingStarCount || ratingStarCount.length === 0) && (
            <p className="text-sm text-muted-foreground">Star distribution not available in current payload.</p>
          )}
        </div>
      </div>

      {/* Good / Bad tags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ThumbsUp className="h-4 w-4" />
            What residents like
          </div>
          <ul className="space-y-2">
            {reviewGood.slice(0, 6).map((g: any, i: number) => (
              <li key={i} className="text-sm text-muted-foreground">
                {g.Name}{" "}
                <span className="text-xs text-muted-foreground/80">
                  ({Math.round(g.Percentage || 0)}%)
                </span>
              </li>
            ))}
            {(!reviewGood || reviewGood.length === 0) && (
              <li className="text-sm text-muted-foreground">Not available in current payload.</li>
            )}
          </ul>
        </div>

        <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ThumbsDown className="h-4 w-4" />
            Areas for improvement
          </div>
          <ul className="space-y-2">
            {reviewBad.slice(0, 6).map((b: any, i: number) => (
              <li key={i} className="text-sm text-muted-foreground">
                {b.Name}{" "}
                <span className="text-xs text-muted-foreground/80">
                  ({Math.round(b.Percentage || 0)}%)
                </span>
              </li>
            ))}
            {(!reviewBad || reviewBad.length === 0) && (
              <li className="text-sm text-muted-foreground">Not available in current payload.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Recent reviews */}
      <div className="rounded-xl bg-card p-5 sy-card-shadow space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Recent Reviews</h3>

        <div className="space-y-4">
          {topReviews.slice(0, 6).map((r: any, i: number) => (
            <div key={i} className="border border-border rounded-xl p-4 bg-background/30">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">{r.Name || "User"}</p>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Star className="h-3 w-3" /> {r.Rating ?? "—"}
                </div>
              </div>

              {!!r?.rating_user_persona?.Name && (
                <p className="text-xs text-muted-foreground mt-1">{r.rating_user_persona.Name}</p>
              )}

              <p className="text-sm text-muted-foreground mt-3 line-clamp-4">
                {(r.PositiveDesc || r.NegativeDesc || "").trim()}
              </p>
            </div>
          ))}
          {(!topReviews || topReviews.length === 0) && (
            <p className="text-sm text-muted-foreground">No recent review snippets available in current payload.</p>
          )}
        </div>
      </div>

      {/* Conclusion narrative */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-foreground">Conclusion</h3>
        <NarrativeBlock html={conclusionHtml} />
      </div>
    </section>
  );
};

export default ReviewsSection;
