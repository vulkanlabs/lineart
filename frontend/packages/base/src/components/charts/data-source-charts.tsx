"use client";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
    LineChart,
    Line,
} from "recharts";
import { Skeleton } from "../ui/skeleton";
import { DefaultGridProps, strokeWidth } from "./constants";

const colors = {
    primary: "hsl(var(--primary))",
    muted: "hsl(var(--muted))",
};

type ChartDataProps = {
    chartData: any[];
};

// Shared empty state component for charts
export const EmptyChartState = () => (
    <div className="flex h-[300px] w-full items-center justify-center">
        <p className="text-sm text-muted-foreground">No data available</p>
    </div>
);

// Shared loading state component for charts
export const LoadingChartState = () => (
    <div className="flex h-[300px] w-full flex-col gap-4">
        <Skeleton className="h-full w-full" />
    </div>
);

// Request Volume Chart - Shows number of requests over time
export function RequestVolumeChart({ chartData }: ChartDataProps) {
    if (!chartData || chartData.length === 0) {
        return <EmptyChartState />;
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 25 }}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} />
                <YAxis />
                <Tooltip />
                <CartesianGrid {...DefaultGridProps} />
                <Bar dataKey="value" fill={colors.primary} name="Requests" />
            </BarChart>
        </ResponsiveContainer>
    );
}

// Response Time Chart - Shows average response time in milliseconds
export function ResponseTimeChart({ chartData }: ChartDataProps) {
    if (!chartData || chartData.length === 0) {
        return <EmptyChartState />;
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 25 }}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} />
                <YAxis />
                <Tooltip />
                <CartesianGrid {...DefaultGridProps} />
                <Line
                    type="monotone"
                    dataKey="value"
                    stroke={colors.primary}
                    name="Avg. Response Time (ms)"
                    dot={{ fill: colors.primary }}
                    activeDot={{
                        fill: colors.muted,
                        stroke: colors.primary,
                        strokeWidth: strokeWidth,
                        r: 5,
                    }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}

// Error Rate Chart - Shows percentage of failed requests
export function ErrorRateChart({ chartData }: ChartDataProps) {
    if (!chartData || chartData.length === 0) {
        return <EmptyChartState />;
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 25 }}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} />
                <YAxis unit="%" domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value}%`, "Error Rate"]} />
                <CartesianGrid {...DefaultGridProps} />
                <Line
                    type="monotone"
                    dataKey="value"
                    stroke={colors.primary}
                    name="Error Rate"
                    dot={{ fill: colors.primary }}
                    activeDot={{
                        fill: colors.muted,
                        stroke: colors.primary,
                        strokeWidth: strokeWidth,
                        r: 5,
                    }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}

// Cache Hit Ratio Chart - Shows percentage of requests served from cache
export function CacheHitRatioChart({ chartData }: ChartDataProps) {
    if (!chartData || chartData.length === 0) {
        return <EmptyChartState />;
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 25 }}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} />
                <YAxis unit="%" domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value}%`, "Cache Hit Ratio"]} />
                <CartesianGrid {...DefaultGridProps} />
                <Line
                    type="monotone"
                    dataKey="value"
                    stroke={colors.primary}
                    name="Cache Hit Ratio"
                    dot={{ fill: colors.primary }}
                    activeDot={{
                        fill: colors.muted,
                        stroke: colors.primary,
                        strokeWidth: strokeWidth,
                        r: 5,
                    }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
