// ui/src/lib/print.ts
export const isPrintMode = (): boolean => {
  if (typeof window === "undefined") return false;
  const sp = new URLSearchParams(window.location.search);
  return sp.get("print") === "1";
};