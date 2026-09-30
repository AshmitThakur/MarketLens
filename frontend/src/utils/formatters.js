export const formatScore = (value) => Number(value).toFixed(2);

export const formatGrowth = (value) => `${Number(value).toFixed(2)}%`;

export const formatNumber = (value) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);

export const formatCompactNumber = (value) =>
  new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2
  }).format(value);
