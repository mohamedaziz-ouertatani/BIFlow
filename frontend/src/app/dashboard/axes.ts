// Longest category label (in characters) that fits the bar chart's 110px label column.
const MAX_LABEL_CHARS = 14;

// The review score is a 1-5 rating, so an automatic axis (which rounds up to 8) misleads.
const REVIEW_SCORE_METRIC = "average_review_score";

// Picks a value-axis domain for a metric: bars must start at zero, but a line chart of a
// bounded rating reads better zoomed into its scale.
export function metricAxisDomain(metric: string, chart: "bar" | "line"): [number, number | "auto"] {
  if (metric === REVIEW_SCORE_METRIC) {
    return chart === "bar" ? [0, 5] : [1, 5];
  }
  return [0, "auto"];
}

// Shortens a long category label from the end ("computers_acc…"); the tooltip shows the full name.
export function truncateAxisLabel(label: string): string {
  if (label.length <= MAX_LABEL_CHARS) {
    return label;
  }
  return `${label.slice(0, MAX_LABEL_CHARS - 1)}…`;
}
