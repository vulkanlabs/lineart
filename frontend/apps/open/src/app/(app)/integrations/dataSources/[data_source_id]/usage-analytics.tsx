"use client";

// React and Next.js
import { useState, useEffect } from "react";

// External libraries
import { DateRange } from "react-day-picker";
import { subDays } from "date-fns";

// Vulkan packages
import {
    CacheHitRatioChart,
    DatePickerWithRange,
    ErrorRateChart,
    LoadingChartState,
    RequestVolumeChart,
    ResponseTimeChart,
} from "@vulkanlabs/base";

// Local imports
import {
    fetchDataSourceCacheStatsAction,
    fetchDataSourceMetricsAction,
    fetchDataSourceUsageAction,
} from "./actions";

export default function DataSourceUsageAnalytics({ dataSourceId }: { dataSourceId: string }) {
    // Chart Data States
    const [requestVolume, setRequestVolume] = useState([]);
    const [responseTime, setResponseTime] = useState([]);
    const [errorRate, setErrorRate] = useState([]);
    const [cacheHitRatio, setCacheHitRatio] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Filters & Interactions
    const [dateRange, setDateRange] = useState<DateRange>({
        from: subDays(new Date(), 7),
        to: new Date(),
    });

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }

        setIsLoading(true);

        // Fetch request volume data
        fetchDataSourceUsageAction(dataSourceId, dateRange.from, dateRange.to)
            .then((data) => {
                setRequestVolume(data.requests_by_date);
                setIsLoading(false);
            })
            .catch((error) => {
                console.error("Error fetching request volume:", error);
                setIsLoading(false);
            });

        // Fetch response time and error rate data
        fetchDataSourceMetricsAction(dataSourceId, dateRange.from, dateRange.to)
            .then((data) => {
                setResponseTime(data.avg_response_time_by_date);
                setErrorRate(data.error_rate_by_date);
            })
            .catch((error) => {
                console.error("Error fetching metrics:", error);
            });

        // Fetch cache hit ratio data
        fetchDataSourceCacheStatsAction(dataSourceId, dateRange.from, dateRange.to)
            .then((data) => {
                setCacheHitRatio(data.cache_hit_ratio_by_date);
            })
            .catch((error) => {
                console.error("Error fetching cache stats:", error);
            });
    }, [dataSourceId, dateRange]);

    const charts = [
        {
            title: "Request Volume",
            subtitle: "Number of requests over time",
            data: requestVolume,
            component: RequestVolumeChart,
        },
        {
            title: "Cache Hit Ratio",
            subtitle: "Percentage of requests served from cache",
            data: cacheHitRatio,
            component: CacheHitRatioChart,
        },
        {
            title: "Response Time",
            subtitle: "Average response time in milliseconds",
            data: responseTime,
            component: ResponseTimeChart,
        },
        {
            title: "Error Rate",
            subtitle: "Percentage of failed requests",
            data: errorRate,
            component: ErrorRateChart,
        },
    ];

    return (
        <div className="mt-8">
            <div className="flex flex-col gap-4 mb-6">
                <h2 className="text-2xl font-bold">Usage Analytics</h2>
                <div className="flex gap-4">
                    <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {charts.map((chart) => (
                    <div key={chart.title}>
                        <h3 className="text-lg font-medium mb-1">{chart.title}</h3>
                        <p className="text-sm text-muted-foreground mb-4">{chart.subtitle}</p>
                        {isLoading ? (
                            <LoadingChartState />
                        ) : (
                            <chart.component chartData={chart.data} />
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
