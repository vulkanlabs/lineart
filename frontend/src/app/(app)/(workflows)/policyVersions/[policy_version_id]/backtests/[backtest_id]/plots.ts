import embed, { VisualizationSpec, Config } from "vega-embed";

const defaultHeight = 200;
const defaultWidth = 400;
const chartConfig = {
    font: "Inter",
    fontSize: {
        text: 18,
    },
} as Config;

export function plotStatusDistribution(data, embedId: string) {
    const spec = makeStatusDistributionSpec(data);
    embed(`#${embedId}`, spec, { actions: false });
}

function makeStatusDistributionSpec(data) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        config: chartConfig,
        height: defaultHeight,
        width: defaultWidth,
        data: { values: data },
        encoding: {
            color: {
                field: "status",
                type: "nominal",
            },
            tooltip: [
                {
                    field: "backfill",
                    type: "nominal",
                },
                {
                    field: "status",
                    type: "nominal",
                },
                {
                    field: "count",
                    type: "quantitative",
                },
            ],
            x: {
                field: "backfill",
                type: "nominal",
            },
            y: {
                field: "count",
                stack: "normalize",
                type: "quantitative",
            },
        },
        mark: {
            type: "bar",
        },
    } as VisualizationSpec;
    return spec;
}

export function plotStatusCount(data, embedId: string) {
    const numStatuses = new Set(data.map((datum) => datum.status)).size;
    const spec = makeStatusCountSpec(data, numStatuses);
    embed(`#${embedId}`, spec, { actions: false });
}

function makeStatusCountSpec(data: any, numStatuses: number) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        config: chartConfig,
        height: defaultHeight,
        width: Math.round(defaultWidth / numStatuses),
        data: { values: data },
        encoding: {
            color: {
                field: "status",
                legend: null,
                type: "nominal",
            },
            column: {
                field: "backfill",
                type: "nominal",
            },
            x: {
                field: "status",
                type: "nominal",
            },
            y: {
                field: "count",
                type: "quantitative",
            },
            tooltip: [
                {
                    field: "backfill",
                    type: "nominal",
                },
                {
                    field: "status",
                    type: "nominal",
                },
                {
                    field: "count",
                    type: "quantitative",
                },
            ],
        },
        mark: {
            type: "bar",
        },
    } as VisualizationSpec;
    return spec;
}

export async function plotEventRate(data, backfills, elemId: string) {
    const shortBackfillIDs = backfills.map((backfill) => backfill.backfill_id.slice(0, 8));
    const spec = makeEventRateSpec(data, shortBackfillIDs);
    embed(`#${elemId}`, spec, { actions: false });
}

function makeEventRateSpec(data: any, backfillShortIDs: string[]) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        config: chartConfig,
        height: defaultHeight,
        width: defaultWidth,
        data: { values: data },
        encoding: {
            x: {
                field: "month",
                timeUnit: "month",
                type: "temporal",
            },
        },
        layer: [
            {
                mark: "rule",
                encoding: {
                    color: {
                        value: "gray",
                    },
                    opacity: {
                        condition: { value: 0.4, param: "hover", empty: false },
                        value: 0,
                    },
                    tooltip: [
                        {
                            field: "count",
                            title: "Count",
                            type: "quantitative",
                        },
                        {
                            field: "rate",
                            title: "% of Ones",
                            type: "quantitative",
                            format: ".2%",
                        },
                        {
                            field: "backfill",
                            title: "Backfill",
                            type: "nominal",
                        },
                        {
                            field: "status",
                            title: "Outcome",
                            type: "nominal",
                        },
                    ],
                },
                params: [
                    {
                        name: "hover",
                        select: {
                            type: "point",
                            fields: ["month"],
                            nearest: true,
                            on: "pointerover",
                            clear: "pointerout",
                        },
                    },
                ],
            },
            {
                encoding: {
                    y: {
                        field: "rate",
                        type: "quantitative",
                    },
                    color: {
                        field: "status",
                        type: "nominal",
                    },
                },
                mark: {
                    type: "line",
                },
                params: [
                    {
                        bind: {
                            input: "select",
                            name: "backfill",
                            options: backfillShortIDs,
                        },
                        name: "param_2",
                        select: {
                            fields: ["backfill"],
                            type: "point",
                        },
                        value: backfillShortIDs[0],
                    },
                ],
            },
        ],
        transform: [
            {
                filter: {
                    param: "param_2",
                },
            },
            {
                as: "rate",
                calculate: "datum.ones/(datum.count)",
            },
        ],
    } as VisualizationSpec;
    return spec;
}

export function plotTargetDistributionPerOutcome(data, outputElementId: string) {
    const numStatuses = new Set(data.map((datum) => datum.status)).size;
    const spec = makeTargetDistributionPerOutcomeSpec(data, numStatuses);
    embed(`#${outputElementId}`, spec, { actions: false });
}

function makeTargetDistributionPerOutcomeSpec(data: any, numOutcomes: number) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        config: chartConfig,
        width: Math.round(defaultWidth / numOutcomes),
        height: defaultHeight,
        data: { values: data },
        encoding: {
            color: {
                field: "status",
                legend: null,
                type: "nominal",
            },
            column: {
                field: "backfill",
                type: "nominal",
            },
            x: {
                field: "status",
                type: "nominal",
            },
            y: {
                field: "rate",
                type: "quantitative",
            },
            tooltip: [
                {
                    field: "count",
                    title: "Count",
                    type: "quantitative",
                },
                {
                    field: "rate",
                    title: "% of Ones",
                    type: "quantitative",
                },
                {
                    field: "backfill",
                    type: "nominal",
                },
                {
                    field: "status",
                    type: "nominal",
                },
            ],
        },
        mark: {
            type: "bar",
        },
        transform: [
            {
                as: "rate",
                calculate: "datum.ones/(datum.count)",
            },
        ],
    } as VisualizationSpec;
    return spec;
}
