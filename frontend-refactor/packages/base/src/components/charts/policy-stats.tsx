"use client";
import { Bar, BarChart, XAxis, YAxis, Line, LineChart, CartesianGrid } from "recharts";

import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "../ui/chart";

import { roundUp } from "../../lib/chart";
import { DefaultGridProps, strokeWidth } from "./constants";

type ChartDataProps = {
    chartData: any[];
};

export function RunsChart({ chartData }: ChartDataProps) {
    const chartConfig = {
        count: {
            label: "Runs",
            color: "#2563eb",
        },
    } satisfies ChartConfig;

    const sorted = [...chartData].sort((a: any, b: any) => dateDiff(a, b));
    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sorted}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line dataKey="count" stroke="var(--color-count)" strokeWidth={strokeWidth} />
            </LineChart>
        </ChartContainer>
    );
}

export function RunErrorRateChart({ chartData }: ChartDataProps) {
    const chartConfig = {
        error_rate: {
            label: "Error Rate",
            color: "#EF5350",
        },
    } satisfies ChartConfig;
    const sortedData = [...chartData]
        .sort((a: any, b: any) => dateDiff(a, b))
        .map((data: any) => ({
            ...data,
            error_rate: Math.round(data.error_rate * 100) / 100,
        }));
    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                    dataKey="error_rate"
                    stroke="var(--color-error_rate)"
                    strokeWidth={strokeWidth}
                />
            </LineChart>
        </ChartContainer>
    );
}

export function RunDurationStatsChart({ chartData }: ChartDataProps) {
    const sortedData = [...chartData].sort((a: any, b: any) => dateDiff(a, b));
    const chartConfig = {
        min_duration: {
            label: "Min",
            color: "hsl(var(--chart-1))",
        },
        max_duration: {
            label: "Max",
            color: "hsl(var(--chart-2))",
        },
        avg_duration: {
            label: "Average",
            color: "hsl(var(--chart-3))",
        },
    } satisfies ChartConfig;

    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                <Line
                    dataKey="min_duration"
                    stroke="var(--color-min_duration)"
                    strokeWidth={strokeWidth}
                />
                <Line
                    dataKey="avg_duration"
                    stroke="var(--color-avg_duration)"
                    strokeWidth={strokeWidth}
                />
                <Line
                    dataKey="max_duration"
                    stroke="var(--color-max_duration)"
                    strokeWidth={strokeWidth}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
        </ChartContainer>
    );
}

export function AvgDurationByStatusChart({ chartData }: ChartDataProps) {
    const runStatusChartConfig = {
        FAILURE: {
            label: "Failure",
            color: "hsl(var(--chart-1))",
        },
        SUCCESS: {
            label: "Success",
            color: "hsl(var(--chart-2))",
        },
        STARTED: {
            label: "Started",
            color: "hsl(var(--chart-3))",
        },
        PENDING: {
            label: "Pending",
            color: "hsl(var(--chart-4))",
        },
    } satisfies ChartConfig;

    const sortedData = [...chartData].sort((a: any, b: any) => dateDiff(a, b));
    return (
        <ChartContainer config={runStatusChartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={0}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Line dataKey="SUCCESS" stroke="var(--color-SUCCESS)" strokeWidth={strokeWidth} />
                <Line dataKey="FAILURE" stroke="var(--color-FAILURE)" strokeWidth={strokeWidth} />
            </LineChart>
        </ChartContainer>
    );
}

// Outcome occurrences
export function RunOutcomesChart({ chartData }: ChartDataProps) {
    const possibleOutcomes = parseOutcomes(chartData);
    const chartConfig = outcomeChartConfig(possibleOutcomes);
    const sortedData = formatOutcomesData(chartData, possibleOutcomes, "count");

    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                {possibleOutcomes.map((outcome) => (
                    <Line
                        key={outcome}
                        dataKey={`${outcome}`}
                        stroke={`var(--color-${outcome})`}
                        strokeWidth={strokeWidth}
                    />
                ))}
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
        </ChartContainer>
    );
}

// Outcome Distribution
export function RunOutcomeDistributionChart({ chartData }: ChartDataProps) {
    const possibleOutcomes = parseOutcomes(chartData);
    const chartConfig = outcomeChartConfig(possibleOutcomes);
    const sortedData = formatOutcomesData(chartData, possibleOutcomes, "percentage");

    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <BarChart accessibilityLayer data={sortedData}>
                <CartesianGrid {...DefaultGridProps} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                />
                <YAxis type="number" domain={[0, 100]} tickMargin={5} />
                {possibleOutcomes.map((outcome) => (
                    <Bar
                        key={outcome}
                        dataKey={`${outcome}`}
                        fill={`var(--color-${outcome})`}
                        stackId={"a"}
                        fillOpacity={0.8}
                    />
                ))}
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
            </BarChart>
        </ChartContainer>
    );
}

// Create a chart config object with a key for each possible outcome
function outcomeChartConfig(outcomes: string[]) {
    return {
        ...outcomes.reduce(
            (acc: any, outcome) => {
                acc[outcome] = {
                    label: outcome,
                    color: `hsl(var(--chart-${(outcomes.indexOf(outcome) % 5) + 1}))`,
                };
                return acc;
            },
            {} as Record<string, any>,
        ),
    } as ChartConfig;
}

// Outcome series are created using a pivot operation, which produces
// weird names due to the multiindex involved.
type OutcomeSeriesType = "count" | "percentage";
function formatOutcomesData(data: any[], outcomes: string[], series: OutcomeSeriesType) {
    return [...data]
        .sort((a, b) => dateDiff(a, b))
        .map((data) => {
            return {
                date: data["date,"],
                ...outcomes.reduce(
                    (acc: any, outcome) => {
                        acc[outcome] = data[`${series},${outcome}`];
                        return acc;
                    },
                    {} as Record<string, any>,
                ),
            };
        });
}

function parseOutcomes(data: any[]) {
    if (data?.length === 0) {
        return [];
    }
    const entry = data[0];
    const keys = Object.keys(entry)
        .filter((key) => key !== "date" && key.startsWith("count"))
        .map((key) => key.replace("count,", ""));
    return keys;
}

function dateDiff(a: any, b: any) {
    return new Date(a.date).valueOf() - new Date(b.date).valueOf();
}
