export const roundUp = (dataMax: number, factor: number = 1.05) =>
    roundToNearestTen(dataMax * factor);

export const roundToNearestTen = (num: number) => Math.ceil(num / 10) * 10;
