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

// Price Trend
export const priceTrend = json2.priceTrend.reverse();

// Nearby Localities
export const nearbyLocalities = json2.locationRates;

// Market Supply
export const marketSupply = json1.marketSupply;

// Rental Stats
export const rentalStats = json1.rentalStats.rentalBHKStats;

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
export const topReviews = json1.ratingReview.topReviews?.slice(0, 6) || [];
export const reviewGood = json1.ratingReview.good || [];
export const reviewBad = json1.ratingReview.bad || [];
export const ratingStarCount = json1.ratingReview.ratingStarCount || [];

// Attributes
export const positiveAttributes = overview.localityAttributes?.filter((a: any) => a.attributeType === "Positive") || [];
export const negativeAttributes = overview.localityAttributes?.filter((a: any) => a.attributeType === "Negative") || [];

// Locality images
export const localityImages = overview.localityImages?.[0]?.allimages || [];

// --- Narratives (HTML) ---
export const narratives = data.narratives || {};
