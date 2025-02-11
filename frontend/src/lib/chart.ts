export const roundUp = (dataMax: number, factor: number = 1.1) =>
    Math.round(Math.ceil(dataMax / 10) * 10 * factor);

// roundToNearestTen(5) => 10
export const roundToNearestTen = (num: number) => Math.ceil(num / 10) * 10;

export const niceMargin = (dataMax: number) => {
    const rounded = roundUp(dataMax);
    return roundToNearestTen(rounded);
}