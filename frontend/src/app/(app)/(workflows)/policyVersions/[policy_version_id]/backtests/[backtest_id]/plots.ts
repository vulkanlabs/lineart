import embed, { VisualizationSpec } from "vega-embed";

export function plotStatusDistribution(data) {
    const spec = makeStatusDistributionSpec(data);
    embed("#status_distribution", spec, { actions: false });
}

function makeStatusDistributionSpec(data) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        width: 400,
        height: 200,
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
                field: "count",
                stack: "normalize",
                type: "quantitative",
            },
            y: {
                field: "backfill",
                type: "nominal",
            },
        },
        mark: {
            type: "bar",
        },
    } as VisualizationSpec;
    return spec;
}

export function plotStatusCount(data) {
    const numStatuses = new Set(data.map((datum) => datum.status)).size;
    const spec = makeStatusCountSpec(data, numStatuses);
    embed("#status_count", spec, { actions: false });
}

function makeStatusCountSpec(data: any, numStatuses: number) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        width: Math.round(400 / numStatuses),
        height: 200,
        data: { values: data },
        encoding: {
            color: {
                field: "backfill",
                legend: null,
                type: "nominal",
            },
            column: {
                field: "status",
                type: "nominal",
            },
            x: {
                field: "backfill",
                type: "nominal",
            },
            y: {
                field: "count",
                type: "quantitative",
            },
        },
        mark: {
            type: "bar",
        },
    } as VisualizationSpec;
    return spec;
}

export async function plotEventRate(data, backfills) {
    const shortBackfillIDs = backfills.map((backfill) => backfill.backfill_id.slice(0, 8));
    const spec = makeEventRateSpec(data, shortBackfillIDs);
    embed("#event_rate", spec, { actions: false });
}

function makeEventRateSpec(data: any, backfillShortIDs: string[]) {
    const spec = {
        $schema: "https://vega.github.io/schema/vega-lite/v5.20.1.json",
        width: 400,
        height: 200,
        data: { values: data },
        encoding: {
            color: {
                field: "status",
                type: "nominal",
            },
            x: {
                field: "month",
                timeUnit: "month",
                type: "temporal",
            },
            y: {
                field: "rate",
                type: "quantitative",
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
        width: Math.round(400 / numOutcomes),
        height: 200,
        data: { values: data },
        encoding: {
            color: {
                field: "backfill",
                legend: null,
                type: "nominal",
            },
            column: {
                field: "status",
                type: "nominal",
            },
            x: {
                field: "backfill",
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
