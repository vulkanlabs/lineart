"use client";

import React, { useState, useEffect } from "react";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";


export default function Page({ params }) {
    const [runs, setRuns] = useState([]);

    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    const fetchRuns = async () => {
        try {
            const response = await fetch(new URL(`/policies/${params.policy_id}/runs`, baseUrl));
            const data = await response.json();
            setRuns(data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        fetchRuns();
        const runsInterval = setInterval(fetchRuns, 2000);
        return () => clearInterval(runsInterval);
    }, []);

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">

            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Execuções</h1>
                </div>
                <RunsTable runs={runs} />
            </div>
        </div>
    );
}


function RunStatus({ value }) {
    const getColor = (status) => {
        switch (status) {
            case "SUCCESS":
                return "green";
            case "FAILURE":
                return "red";
            default:
                return "gray";
        }
    };

    return (
        <p className={`w-fit p-[0.3em] rounded-lg bg-${getColor(value)}-200`}>
            {value}
        </p>
    );
}


function RunsTable({ runs }) {
    return (
        <Table>
            <TableCaption>Execuções.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Resultado</TableHead>
                    <TableHead>Criada Em</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {runs.map((run) => (
                    <TableRow key={run.run_id}>
                        <TableCell>{run.run_id}</TableCell>
                        <TableCell>{run.policy_version_id}</TableCell>
                        <TableCell><RunStatus value={run.status} /></TableCell>
                        <TableCell>{run.result == null || run.result == "" ? "-" : run.result}</TableCell>
                        <TableCell>{run.created_at}</TableCell>
                    </TableRow>

                ))}
            </TableBody>
        </Table >
    );

}
