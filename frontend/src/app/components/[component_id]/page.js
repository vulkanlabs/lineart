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
    const [componentVersions, setComponentVersions] = useState([]);

    const refreshTime = 5000;
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    const fetchComponentVersions = async () => {
        try {
            const componentVersionsResponse = await fetch(new URL(`/components/${params.component_id}/versions`, baseUrl));
            const componentVersionsData = await componentVersionsResponse.json();
            setComponentVersions(componentVersionsData);
        } catch (error) {
            console.error(error);
        }
    };
    useEffect(() => {
        fetchComponentVersions();
        const policiesInterval = setInterval(fetchComponentVersions, refreshTime);
        return () => clearInterval(policiesInterval);
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
                    <h3 className="text-sm text-muted-foreground">Políticas que utilizam esse Componente</h3>
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
                        <TableCell>{entry.component_version}</TableCell>
                        <TableCell>{entry.alias}</TableCell>
                        <TableCell>{entry.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table >
    );
}


