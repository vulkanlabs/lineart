
import { Bar, BarChart, XAxis, YAxis, Line, LineChart } from "recharts";

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
} satisfies ChartConfig

export function RunsChart({ chartData }) {
    const chartConfig = {
        count: {
            label: "Runs",
            color: "#2563eb",
        },
    } satisfies ChartConfig;

    return (
        <ChartContainer config={chartConfig} className="h-full w-full" >
            <BarChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, roundUp]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="count" fill="var(--color-count)" radius={4} />
            </BarChart>
        </ChartContainer>
    );
}

export function RunsByStatusChart({ chartData }) {
    return (
        <ChartContainer config={runStatusChartConfig} className="h-full w-full" >
            <BarChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, roundUp]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="SUCCESS" radius={0} stackId="a" fill="var(--color-SUCCESS)" />
                <Bar dataKey="FAILURE" radius={0} stackId="a" fill="var(--color-FAILURE)" />
                <Bar dataKey="STARTED" radius={0} stackId="a" fill="var(--color-STARTED)" />
                <Bar dataKey="PENDING" radius={0} stackId="a" fill="var(--color-PENDING)" />
            </BarChart>
        </ChartContainer>
    );
}

export function RunDurationStatsChart({ chartData }) {
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
        }
    } satisfies ChartConfig;

    return (
        <ChartContainer config={chartConfig} className="h-full w-full" >
            <LineChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, roundUp]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Line dataKey="min_duration" stroke="var(--color-min_duration)" />
                <Line dataKey="avg_duration" stroke="var(--color-avg_duration)" />
                <Line dataKey="max_duration" stroke="var(--color-max_duration)" />
            </LineChart>
        </ChartContainer>
    );
}


export function AvgDurationByStatusChart({ chartData }) {
    return (
        <ChartContainer config={runStatusChartConfig} className="h-full w-full" >
            <LineChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, roundUp]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Line dataKey="SUCCESS" stroke="var(--color-SUCCESS)" />
                <Line dataKey="FAILURE" stroke="var(--color-FAILURE)" />
                <Line dataKey="STARTED" stroke="var(--color-STARTED)" />
                <Line dataKey="PENDING" stroke="var(--color-PENDING)" />
            </LineChart>
        </ChartContainer>
    );
}