export type BacktestPlotData = {
    distributionPerOutcome?: any;
    targetMetrics?: any;
    timeMetrics?: any;
    eventRate?: any;
};

export type BacktestMetrics = {
    distributionPerOutcome: boolean;
    targetMetrics: boolean;
    timeMetrics: boolean;
    eventRate: boolean;
};
