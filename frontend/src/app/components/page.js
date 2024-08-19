"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from 'next/navigation';
import { fetchComponents } from "@/lib/api";
import { EmptyAssetTable } from "@/components/empty-asset-table";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export default function PolicyPageBody() {
    const [components, setComponents] = useState([]);
    const refreshTime = 5000;
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    useEffect(() => {
        const refreshComponents = () => fetchComponents(serverUrl)
            .then((data) => setComponents(data))
            .catch((error) => console.error("Error fetching components", error));

        refreshComponents();
        const comInterval = setInterval(refreshComponents, refreshTime);
        return () => clearInterval(comInterval);
    }, [serverUrl]);

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Componentes</h1>
            </div>
            <ComponentPageContent components={components} />
        </div>
    );
}

function ComponentPageContent({ components }) {
    return (
        <div>
            {components.length > 0 ? <ComponentsTable components={components} /> :
                <EmptyAssetTable
                    title="Você ainda não tem componentes criados"
                    description="Crie um componente para começar" />}
        </div>
    );
}

function ComponentsTable({ components }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Lista dos seus componentes criados.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Descrição</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {components.map((entry) => (
                    <TableRow key={entry.component_id} className="cursor-pointer" onClick={() => router.push(`/components/${entry.component_id}`)} >
                        <TableCell>{entry.component_id}</TableCell>
                        <TableCell>{entry.name}</TableCell>
                        <TableCell> - </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table >
    );
}
