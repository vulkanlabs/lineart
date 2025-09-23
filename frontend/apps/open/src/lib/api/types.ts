export interface DateRange {
    from?: Date;
    to?: Date;
}

export interface MetricsData {
    runsCount: any[];
    errorRate: any[];
    runDurationStats: any[];
    runDurationByStatus: any[];
}

export interface RunOutcomes {
    runOutcomes: any[];
}

export interface RunsResponse {
    runs: any[] | null;
}

export interface DataSourceUsage {
    usage: any[];
}

export interface DataSourceMetrics {
    metrics: any[];
}

export interface DataSourceCacheStats {
    cacheStats: any;
}
