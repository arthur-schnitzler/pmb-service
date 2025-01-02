function dateToCoordinates(isoDate, minYear = 1500, maxYear = 1800) {
  // Parse the ISO date
  const date = new Date(isoDate);
  if (isNaN(date)) {
    throw new Error("Invalid date format");
  }

  // Extract year, month, and day
  const year = date.getUTCFullYear();
  const month = date.getUTCMonth() + 1; // Months are 0-based
  const day = date.getUTCDate();

  // Map year to latitude (-90 to 90) with larger gaps between years
  const yearFactor = (year - minYear) / (maxYear - minYear);
  const latitude = yearFactor * 180 - 90;

  // Map month and day to longitude (-180 to 180)
  const maxMonth = 12;
  const maxDay = 31; // Approximation for simplicity
  const monthFactor = (month - 1) / (maxMonth - 1);
  const dayFactor = (day - 1) / (maxDay - 1);
  const longitude = ((monthFactor + dayFactor) / 2) * 360 - 180;

  return { lat: latitude, lng: longitude };
}

function scaleToRange(
  x,
  originalMin = 1,
  originalMax = 10,
  targetMin = 0,
  targetMax = 250
) {
  return (
    Math.round(
      ((x - originalMin) * (targetMax - targetMin)) /
        (originalMax - originalMin)
    ) + targetMin
  );
}

function mapValueToColor(value) {
  if (value < 1 || value > 10) {
    return [0, 0, 0];
  }

  // Normalize the value to a range of 0 to 1
  const normalized = (value - 1) / 9;

  // Define the gradient colors (red -> yellow -> green)
  const startColor = [255, 0, 0]; // Red
  const midColor = [255, 255, 0]; // Yellow
  const endColor = [0, 255, 0]; // Green

  let color;
  if (normalized <= 0.5) {
    // Interpolate between startColor and midColor
    const t = normalized * 2; // Scale to [0, 1]
    color = startColor.map((start, i) =>
      Math.round(start + t * (midColor[i] - start))
    );
  } else {
    // Interpolate between midColor and endColor
    const t = (normalized - 0.5) * 2; // Scale to [0, 1]
    color = midColor.map((mid, i) => Math.round(mid + t * (endColor[i] - mid)));
  }

  // Convert to RGB format
  return [color[0], color[1], color[2]];
}
