import reportPayload from "@/data/report_payload.json";

const data = reportPayload as any;
const meta = data.meta;
const json1 = data.sources.json1_locality;
const json2 = data.sources.json2_rates;
const overview = json1.localityOverviewData;

export const localityName = meta.locality;
export const cityName = meta.city;
export const micromarket = meta.micromarket;

// TODO: Replace with dynamic label if you start storing report period in meta/computed.
export const reportDate = "Feb 2026";

// Assets
export const polygonThumbnail = data.assets.polygon_thumbnail_url;

// Executive Summary
export const askingPrice = json2.marketOverview.askingPrice;
export const registrationRate = json2.marketOverview.registrationRate;
export const avgRating = json1.ratingReviewData.AvgRating;
export const reviewCount = json1.ratingReviewData.ReviewCount;
export const totalProjects = overview.totalprojects;
export const totalListings = overview.totallistings;
export const saleCount = overview.saleCount;
export const rentCount = overview.rentCount;

// Price Trend (avoid mutating original array)
export const priceTrend = Array.isArray(json2.priceTrend) ? [...json2.priceTrend].reverse() : [];

// Nearby Localities
export const nearbyLocalities = json2.locationRates;

// Market Supply
export const marketSupply = json1.marketSupply;

// Rental Stats
export const rentalStats = json1.rentalStats?.rentalBHKStats ?? [];

// Liveability Indices
export const indices = json1.indices;

// Demand Supply
export const demandSupplySale = json1.demandSupply.sale;
export const demandSupplyRent = json1.demandSupply.rent;

// Property Types and Status
export const propertyTypes = json2.propertyTypes;
export const propertyStatus = json2.propertyStatus;

// Top Projects
export const topProjectsByTxn = json2.topProjects.byTransactions.projects;
export const topProjectsByListing = json2.topProjects.byListingRates.projects;

// Registration
export const govtRegistration = json1.govtRegistration;

// FIX: topDevelopers.byTransactions is an object; developers is the array
const topDevelopersByTxnRaw =
  data.sources.json1_locality?.topDevelopersByTxn ??
  json2.topDevelopers?.byTransactions?.developers ??
  json2.topDevelopers?.byTransactions ??
  [];

export const topDevelopersByTxn = Array.isArray(topDevelopersByTxnRaw) ? topDevelopersByTxnRaw : [];

// Reviews
export const topReviews = json1.ratingReview?.topReviews?.slice(0, 6) || [];
export const reviewGood = json1.ratingReview?.good || [];
export const reviewBad = json1.ratingReview?.bad || [];
export const ratingStarCount = json1.ratingReview?.ratingStarCount || [];

// Attributes
export const positiveAttributes =
  overview.localityAttributes?.filter((a: any) => a.attributeType === "Positive") || [];
export const negativeAttributes =
  overview.localityAttributes?.filter((a: any) => a.attributeType === "Negative") || [];

// Locality images
export const localityImages = overview.localityImages?.[0]?.allimages || [];

// --- Narratives (HTML) ---
export const narratives = data.narratives || {};

export const marketSnapshotNarrative =
  narratives?.page4_market_snapshot?.narrative ||
  narratives?.["page4_market_snapshot.narrative"] ||
  "";
// --- Landmarks (for Liveability cards) ---
type LandmarksRaw = Record<string, any[]>;

export const landmarksRaw: LandmarksRaw =
  json1?.landmarks ??
  data?.page3_liveability?.data?.landmarks ??
  {};

// Normalize keys to make matching robust (case/space/underscore differences)
const norm = (s: string) =>
  (s || "")
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[_\s]+/g, " ")
    .replace(/[^\w\s]/g, ""); // drop punctuation

const resolveCategoryKey = (raw: LandmarksRaw, desired: string): string | null => {
  if (!raw || typeof raw !== "object") return null;

  const desiredN = norm(desired);
  const keys = Object.keys(raw);

  // 1) Exact normalized match
  for (const k of keys) {
    if (norm(k) === desiredN) return k;
  }

  // 2) Fuzzy: contains (handles cases like "Bus Stop (Near)" etc.)
  for (const k of keys) {
    const kn = norm(k);
    if (kn.includes(desiredN) || desiredN.includes(kn)) return k;
  }

  return null;
};

const toLandmarkName = (x: any): string => {
  if (!x) return "";
  return (
    x.landmarkname ||
    x.landmarkName ||
    x.name ||
    x.searchtext ||
    x.searchText ||
    ""
  ).toString().trim();
};

// Try to sort by distance/priority if present
const toDistance = (x: any): number | null => {
  const candidates = [
    x?.distance,
    x?.dist,
    x?.distanceKm,
    x?.distance_km,
    x?.distanceInKm,
    x?.priority,
    x?.rank,
  ];
  for (const v of candidates) {
    if (v == null) continue;
    const n = Number(v);
    if (!Number.isNaN(n)) return n;
  }
  return null;
};

const pickLandmarks = (raw: LandmarksRaw, categories: string[], limit = 3): string[] => {
  const out: string[] = [];
  const seen = new Set<string>();

  for (const desiredCat of categories) {
    const actualKey = resolveCategoryKey(raw, desiredCat);
    if (!actualKey) continue;

    const arr = raw?.[actualKey];
    if (!Array.isArray(arr) || arr.length === 0) continue;

    // stable sort by distance/rank if available
    const sorted = [...arr].sort((a, b) => {
      const da = toDistance(a);
      const db = toDistance(b);
      if (da == null && db == null) return 0;
      if (da == null) return 1;
      if (db == null) return -1;
      return da - db;
    });

    for (const item of sorted) {
      const nm = toLandmarkName(item);
      if (!nm) continue;
      if (seen.has(nm)) continue;

      seen.add(nm);
      out.push(nm);

      if (out.length >= limit) return out;
    }
  }

  return out;
};

/**
 * STRICT mapping: each index card pulls ONLY from the correct landmark bucket(s)
 * as per your actual payload categories:
 * Hospital, Bus Stop, School, Bank, ATM, Temple, Shopping Mall, Mosque, Park, Post Office
 */
export const indexLandmarks = {
  connectivity: pickLandmarks(landmarksRaw, ["Bus Stop"], 10),
  lifestyle: pickLandmarks(landmarksRaw, ["Shopping Mall"], 10),
  educationhealth: pickLandmarks(landmarksRaw, ["Hospital"], 10),
  livability: pickLandmarks(landmarksRaw, ["Park"], 10),
};