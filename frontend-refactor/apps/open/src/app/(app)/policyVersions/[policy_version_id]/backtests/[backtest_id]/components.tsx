"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { RotateCw, ArrowLeft } from "lucide-react";

import { Button } from "@vulkan/base/ui";
import { ShortenedID } from "@vulkan/base";

import {
    plotStatusCount,
    plotStatusDistribution,
    plotEventRate,
    plotTargetDistributionPerOutcome,
} from "./plots";
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@vulkan/base";

import { BackfillStatus } from "@vulkan/client-open/models/BackfillStatus";

export function BacktestDetailsPage({ policyVersionId, backtest, backfills, plotData }) {
    return (
        <div className="flex flex-col py-4 px-8 gap-12">
            <div className="flex flex-col gap-8">
                <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                    <button className="flex flex-row gap-2 bg-white text-black hover:text-gray-700 text-lg font-bold">
                        <ArrowLeft />
                        Back
                    </button>
                </Link>
                <div className="flex flex-row gap-2 items-center">
                    <div className="text-base font-semibold">Backtest ID:</div>{" "}
                    <p>{backtest.backtest_id}</p>
                </div>
                <BackfillsTableComponent backfills={backfills} />
            </div>
            {backtest.calculate_metrics && (
                <MetricsComponent backfills={backfills} plotData={plotData} />
            )}
        </div>
    );
}

function BackfillsTableComponent({ backfills }) {
    const router = useRouter();

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Backfills</h1>
                <div className="flex gap-4">
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll mt-4">
                <DataTable columns={BackfillColumns} data={backfills} />
            </div>
        </div>
    );
}

const BackfillColumns: ColumnDef<BackfillStatus>[] = [
    {
        accessorKey: "backfill_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("backfill_id")} />,
    },
    {
        accessorKey: "config_variables",
        header: "Config Variables",
        cell: ({ row }) => {
            const content = row.getValue("config_variables");
            const pretty = JSON.stringify(content, null, 2);
            return <div>{pretty}</div>;
        },
    },
    {
        accessorKey: "status",
        header: "Status",
    },
];

function MetricsComponent({ backfills, plotData }) {
    return (
        <div className="flex flex-col gap-8">
            <h1 className="text-lg font-semibold md:text-2xl">Metrics</h1>
            <div className="grid grid-cols-2 gap-4">
                {plotData.distributionPerOutcome && (
                    <OutcomeDistributionMetrics data={plotData.distributionPerOutcome} />
                )}
                {plotData.targetMetrics && <TargetMetrics data={plotData.targetMetrics} />}
                {plotData.timeMetrics && <></>}
                {plotData.eventRate && (
                    <EventRateOverTime data={plotData.event_rate} backfills={backfills} />
                )}
            </div>
        </div>
    );
}

function TargetMetrics({ data }) {
    const elemId = "target_per_outcome";
    plotTargetDistributionPerOutcome(data, elemId);

    return (
        <div className="flex flex-col gap-4">
            <div className="font-semibold">Target Ratio per Outcome</div>
            <div id={elemId} className="flex flex-col items-center"></div>
        </div>
    );
}

function OutcomeDistributionMetrics({ data }) {
    const distributionId = "status_distribution";
    const countId = "status_count";

    plotStatusCount(data, countId);
    plotStatusDistribution(data, distributionId);

    return (
        <>
            <div className="flex flex-col gap-4">
                <div className="font-semibold">Target Count per Outcome</div>
                <div id={countId}></div>
            </div>
            <div className="flex flex-col gap-4">
                <div className="font-semibold">Outcome Distribution</div>
                <div id={distributionId}></div>
            </div>
        </>
    );
}

function EventRateOverTime({ data, backfills }) {
    const elemId = "event_rate";
    plotEventRate(data, backfills, elemId);

    return (
        <div className="flex flex-col gap-4">
            <div className="font-semibold">Event Rate over Time</div>
            <div id={elemId}></div>
        </div>
    );
}
