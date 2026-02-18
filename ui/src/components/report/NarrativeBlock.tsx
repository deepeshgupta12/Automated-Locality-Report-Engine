import React from "react";

/**
 * Renders LLM-generated narrative HTML from payload.narratives.
 * Assumption: HTML is trusted (generated server-side) and constrained by schema.
 */
const NarrativeBlock = ({ html }: { html?: string }) => {
  if (!html) return null;

  return (
    <div
      className="rounded-xl bg-card p-5 sy-card-shadow text-sm text-muted-foreground text-left [&_ul]:list-disc [&_ul]:pl-5 [&_li]:mb-1 [&_p]:mb-2 [&_strong]:text-foreground"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export default NarrativeBlock;
