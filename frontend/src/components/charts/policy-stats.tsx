"use client";
import { XAxis, YAxis, Line, LineChart, CartesianGrid } from "recharts";

import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "@/components/ui/chart";

import { roundUp } from "@/lib/chart";

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

function dateDiff(a, b) {
    return new Date(a.date).valueOf() - new Date(b.date).valueOf();
}

export function RunsChart({ chartData }) {
    const chartConfig = {
        count: {
            label: "Runs",
            color: "#2563eb",
        },
    } satisfies ChartConfig;

    const sorted = chartData.sort((a, b) => dateDiff(a, b));
    return (
        <ChartContainer config={chartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sorted}>
                <CartesianGrid strokeDasharray="3 3" stroke="#999" strokeOpacity={0.5} />
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
                <ChartLegend content={<ChartLegendContent />} />
                <Line dataKey="count" stroke="var(--color-count)" />
            </LineChart>
        </ChartContainer>
    );
}

export function RunsByStatusChart({ chartData }) {
    const sortedData = chartData.sort((a, b) => dateDiff(a, b));
    return (
        <ChartContainer config={runStatusChartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#999" strokeOpacity={0.5} />
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
                <ChartLegend content={<ChartLegendContent />} />
                <Line dataKey="SUCCESS" radius={0} stroke="var(--color-SUCCESS)" />
                <Line dataKey="FAILURE" radius={0} stroke="var(--color-FAILURE)" />
                <Line dataKey="STARTED" radius={0} stroke="var(--color-STARTED)" />
                <Line dataKey="PENDING" radius={0} stroke="var(--color-PENDING)" />
            </LineChart>
        </ChartContainer>
    );
}

export function RunDurationStatsChart({ chartData }) {
    const sortedData = chartData.sort((a, b) => dateDiff(a, b));
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
                <CartesianGrid strokeDasharray="3 3" stroke="#999" strokeOpacity={0.5} />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    interval={0}
                    axisLine={false}
                    padding={{ right: 30 }}
                />
                <YAxis type="number" domain={[0, roundUp]} />
                <Line dataKey="min_duration" stroke="var(--color-min_duration)" />
                <Line dataKey="avg_duration" stroke="var(--color-avg_duration)" />
                <Line dataKey="max_duration" stroke="var(--color-max_duration)" />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
        </ChartContainer>
    );
}

export function AvgDurationByStatusChart({ chartData }) {
    const sortedData = chartData.sort((a, b) => dateDiff(a, b));
    return (
        <ChartContainer config={runStatusChartConfig} className="h-full w-full">
            <LineChart accessibilityLayer data={sortedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#999" strokeOpacity={0.5} />
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
                <Line dataKey="SUCCESS" stroke="var(--color-SUCCESS)" />
                <Line dataKey="FAILURE" stroke="var(--color-FAILURE)" />
            </LineChart>
        </ChartContainer>
    );
}
