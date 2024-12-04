"use client";
import Link from "next/link";
import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@stackframe/stack";
import { RotateCw, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { ShortenedID } from "@/components/shortened-id";
import { fetchBacktestMetrics } from "@/lib/api";

import {
    plotStatusCount,
    plotStatusDistribution,
    plotEventRate,
    plotTargetDistributionPerOutcome,
} from "./plots";
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";

export function BacktestDetailsPage({ policyVersionId, backtest, backfills }) {
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
                <MetricsComponent backtest={backtest} backfills={backfills} />
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

type BackfillStatus = {
    backfill_id: string;
    config_variables: Record<string, any>;
    status: string;
};

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

function MetricsComponent({ backtest, backfills }) {
    const backtestId = backtest.backtest_id;

    const availability = BacktestMetricAvailability({ backtest });

    return (
        <div className="flex flex-col gap-8">
            <h1 className="text-lg font-semibold md:text-2xl">Metrics</h1>
            <div className="grid grid-cols-2 gap-4">
                {availability.distributionPerOutcome && (
                    <OutcomeDistributionMetrics backtestId={backtestId} />
                )}
                {availability.targetMetrics && <TargetMetrics backtestId={backtestId} />}
                {availability.timeMetrics && <></>}
                {availability.eventRate && (
                    <EventRateOverTime backtestId={backtestId} backfills={backfills} />
                )}
            </div>
        </div>
    );
}

type BacktestMetrics = {
    distributionPerOutcome: boolean;
    targetMetrics: boolean;
    timeMetrics: boolean;
    eventRate: boolean;
};

function BacktestMetricAvailability({ backtest }): BacktestMetrics {
    if (!backtest.calculate_metrics) {
        return {
            distributionPerOutcome: false,
            targetMetrics: false,
            timeMetrics: false,
            eventRate: false,
        };
    }

    return {
        distributionPerOutcome: true,
        targetMetrics: backtest.target_column,
        timeMetrics: backtest.time_column,
        eventRate: backtest.time_column && backtest.target_column,
    };
}

function TargetMetrics({ backtestId }) {
    const user = useUser();
    const elemId = "target_per_outcome";

    useEffect(() => {
        fetchBacktestMetrics(user, backtestId, true)
            .then((data) => {
                plotTargetDistributionPerOutcome(data, elemId);
            })
            .catch((error) => {
                console.error(error);
            });
    }, []);

    return (
        <div className="flex flex-col gap-4">
            <div className="font-semibold">Target Ratio per Outcome</div>
            <div id={elemId} className="flex flex-col items-center"></div>
        </div>
    );
}

function OutcomeDistributionMetrics({ backtestId }) {
    const user = useUser();

    const distributionId = "status_distribution";
    const countId = "status_count";

    useEffect(() => {
        fetchBacktestMetrics(user, backtestId, false)
            .then((data) => {
                plotStatusCount(data, countId);
                plotStatusDistribution(data, distributionId);
            })
            .catch((error) => {
                console.error(error);
            });
    }, []);

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

function EventRateOverTime({ backtestId, backfills }) {
    const user = useUser();

    useEffect(() => {
        fetchBacktestMetrics(user, backtestId, true, true)
            .then((data) => {
                plotEventRate(data, backfills);
            })
            .catch((error) => {
                console.error(error);
            });
    }, []);

    return (
        <div className="flex flex-col gap-4">
            <div className="font-semibold">Event Rate over Time</div>
            <div id="event_rate"></div>
        </div>
    );
}
