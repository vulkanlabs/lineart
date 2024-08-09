"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from 'next/navigation';

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
    const [policyVersions, setPolicyVersions] = useState([]);
    const [runs, setRuns] = useState([]);

    const refreshTime = 5000;
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    const fetchPolicyVersions = async () => {
        try {
            const policyResponse = await fetch(new URL(`/policies/${params.policy_id}`, baseUrl));
            const policyData = await policyResponse.json();
            const policyVersionsResponse = await fetch(new URL(`/policies/${params.policy_id}/versions`, baseUrl));
            const policyVersionsData = await policyVersionsResponse.json();
            policyVersionsData.forEach((policyVersion) => {
                if (policyVersion.policy_version_id === policyData.active_policy_version_id) {
                    policyVersion.status = "ativa";
                } else {
                    policyVersion.status = "inativa";
                }
            });
            setPolicyVersions(policyVersionsData);
        } catch (error) {
            console.error(error);
        }
    };

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
        fetchPolicyVersions()
        fetchRuns()
        const policiesInterval = setInterval(fetchPolicyVersions, refreshTime);
        const runsInterval = setInterval(fetchRuns, 2000);
        return () => {
            clearInterval(policiesInterval);
            clearInterval(runsInterval);
        }
    }, []);

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Versões</h1>
                </div>
                <PolicyVersionsTable policyVersions={policyVersions} />
            </div>
            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Execuções</h1>
                </div>
                <RunsTable runs={runs} />
            </div>
        </div>
    );
}


function PolicyVersionStatus({ value }) {
    if (value === "ativa") {
        return (
            <p className={`w-fit p-[0.3em] rounded-lg bg-green-200`}>
                {value}
            </p>
        );
    }
    return (
        <p className={`w-fit p-[0.3em] rounded-lg bg-gray-200`}>
            {value}
        </p>
    );
}


function PolicyVersionsTable({ policyVersions }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Versões disponíveis.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Componentes</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Criada Em</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {policyVersions.map((policyVersion) => (
                    <TableRow
                        key={policyVersion.policy_version_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/policies/${policyVersion.policy_id}/workflow`)}
                    >
                        <TableCell>{policyVersion.policy_version_id}</TableCell>
                        <TableCell>{policyVersion.alias}</TableCell>
                        <TableCell>{policyVersion.component_version_ids.length > 0 ? policyVersion.component_version_ids : "-"}</TableCell>
                        <TableCell><PolicyVersionStatus value={policyVersion.status} /></TableCell>
                        <TableCell>{policyVersion.created_at}</TableCell>
                    </TableRow>

                ))}
            </TableBody>
        </Table >
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


async function getGraphData(policyId) {
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const policyUrl = new URL(`/policies/${policyId}`, baseUrl);
    const policyVersionId = await fetch(policyUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch policy version id for policy",
                { cause: error });
        })
        .then((response) => {
            if (response.active_policy_version_id === null) {
                throw new Error(`Policy ${policyId} has no active version`);
            }
            return response.active_policy_version_id;
        });


    if (policyVersionId === null) {
        throw new Error(`Policy ${policyId} has no active version`);
    }

    const versionUrl = new URL(`/policyVersions/${policyVersionId}`, baseUrl);
    const data = await fetch(versionUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch graph data", { cause: error });
        });
    return data;
}