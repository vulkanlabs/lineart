"use client";
import Link from "next/link";
import React, { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@stackframe/stack";
import { RotateCw, ArrowLeft } from "lucide-react";
import embed from "vega-embed";

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

export function BacktestDetailsPage({ policyVersionId, backtest }) {
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
                <BackfillsTableComponent backfills={backtest.backfills} />
            </div>
            <MetricsComponent backtestId={backtest.backtest_id} backfills={backtest.backfills} />
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
            <div className="max-h-[30vh] overflow-scroll">
                <BackfillsTable backfills={backfills} />
            </div>
        </div>
    );
}

function BackfillsTable({ backfills }) {
    return (
        <Table>
            <TableCaption>Backfill jobs.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Config Variables</TableHead>
                    <TableHead>Status</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {backfills.map((backfill) => (
                    <TableRow key={backfill.backfill_id}>
                        <TableCell>
                            <ShortenedID id={backfill.backfill_id} />
                        </TableCell>
                        <TableCell>{JSON.stringify(backfill.config_variables)}</TableCell>
                        <TableCell>{backfill.status}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

async function MetricsComponent({ backtestId, backfills }) {
    const [baseData, setBaseData] = useState([]);
    const user = useUser();

    function loadBaseData() {
        fetchBacktestMetrics(user, backtestId, true)
            .then((data) => {
                setBaseData(data);
            })
            .catch((error) => {
                console.error(error);
            });
    }

    function loadTimedData() {
        fetchBacktestMetrics(user, backtestId, true, true)
            .then((data) => {
                setBaseData(data);
            })
            .catch((error) => {
                console.error(error);
            });
    }

    useEffect(() => {
        loadBaseData();
        loadTimedData();
    }, []);

    async function plotStatusDistribution() {
        const spec = makeStatusDistributionSpec(baseData);
        embed("#status_distribution", { ...spec }, { actions: false });
    }

    async function plotEventRate() {
        const shortBackfillIDs = backfills.map((backfill) => backfill.backfill_id.slice(0, 8));
        const spec = makeEventRateSpec(baseData, shortBackfillIDs);
        embed("#event_rate", { ...spec }, { actions: false });
    }

    useEffect(() => {
        plotStatusDistribution();
        plotEventRate();
    }, [baseData]);

    return (
        <div className="flex flex-col gap-8">
            <h1 className="text-lg font-semibold md:text-2xl">Metrics</h1>
            <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-4">
                    <div className="font-semibold">Status Distribution</div>
                    <div id="status_distribution"></div>
                </div>
                <div className="flex flex-col gap-4">
                    <div className="font-semibold">Event Rate</div>
                    <div id="event_rate"></div>
                </div>
            </div>
        </div>
    );
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
    };
    return spec;
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
                calculate: "datum.ones/(datum.ones + datum.zeros)",
            },
        ],
    };
    return spec;
}
