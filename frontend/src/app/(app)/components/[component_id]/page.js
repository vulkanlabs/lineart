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

import { fetchComponentVersions, fetchComponentVersionUsage } from "@/lib/api";


export default function Page({ params }) {
    const [componentVersions, setComponentVersions] = useState([]);
    const [componentVersionDependencies, setComponentVersionDependencies] = useState([]);

    const refreshTime = 15000;
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    const refreshComponentVersions = async () => {
        fetchComponentVersions(serverUrl, params.component_id)
            .then((data) => setComponentVersions(data))
            .catch((error) => console.error(error));
    };

    const refreshComponentVersionDependencies = async () => {
        const dependencies = fetchComponentVersionUsage(serverUrl, params.component_id)
            .then((data) => setComponentVersionDependencies(data))
            .catch((error) => console.error(error));
    };

    useEffect(() => {
        refreshComponentVersions();
        refreshComponentVersionDependencies();
        const policiesInterval = setInterval(refreshComponentVersions, refreshTime);
        const dependenciesInterval = setInterval(refreshComponentVersionDependencies, refreshTime);
        return () => {
            clearInterval(policiesInterval);
            clearInterval(dependenciesInterval);
        };
    }, []);

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Versões</h1>
                </div>
                <ComponentVersionsTable versions={componentVersions} />
            </div>
            <div>
                <div className="flex flex-col justify-start">
                    <h1 className="text-lg font-semibold md:text-2xl">Utilização</h1>
                    <ComponentVersionDependenciesTable entries={componentVersionDependencies} />
                </div>
            </div>
        </div>
    );
}


function ComponentVersionsTable({ versions }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Versões disponíveis.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Input Schema</TableHead>
                    <TableHead>Instance Params Schema</TableHead>
                    <TableHead>Criada Em</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {versions.map((entry) => (
                    <TableRow
                        key={entry.component_version_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/components/${entry.component_id}/versions/${entry.component_version_id}/workflow`)}
                    >
                        <TableCell>{entry.component_version_id}</TableCell>
                        <TableCell>{entry.alias}</TableCell>
                        <TableCell>{entry.input_schema}</TableCell>
                        <TableCell>{entry.instance_params_schema}</TableCell>
                        <TableCell>{entry.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table >
    );
}


function ComponentVersionDependenciesTable({ entries }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Políticas que usam este componente.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID do Componente</TableHead>
                    <TableHead>Versão do Componente</TableHead>
                    <TableHead>ID da Política</TableHead>
                    <TableHead>Nome da Política</TableHead>
                    <TableHead>Versão da Política</TableHead>
                    <TableHead>Tag da Versão</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {entries.map((entry) => (
                    <TableRow
                        key={entry.component_version_id + entry.policy_version_id}
                    >
                        <TableCell>{entry.component_version_id}</TableCell>
                        <TableCell>{entry.component_version_alias}</TableCell>
                        <TableCell>{entry.policy_id}</TableCell>
                        <TableCell>{entry.policy_name}</TableCell>
                        <TableCell>{entry.policy_version_id}</TableCell>
                        <TableCell>{entry.policy_version_alias}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table >
    );
}