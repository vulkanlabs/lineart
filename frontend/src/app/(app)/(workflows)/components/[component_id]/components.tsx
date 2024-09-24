"use client";

import { useRouter } from "next/navigation";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export function ComponentVersionsTable({ versions }) {
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
                        onClick={() =>
                            router.push(
                                `/components/${entry.component_id}/versions/${entry.component_version_id}/workflow`,
                            )
                        }
                    >
                        <TableCell>{entry.component_version_id}</TableCell>
                        <TableCell>{entry.alias}</TableCell>
                        <TableCell>{entry.input_schema}</TableCell>
                        <TableCell>{entry.instance_params_schema}</TableCell>
                        <TableCell>{entry.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function ComponentVersionDependenciesTable({ entries }) {
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
                    <TableRow key={entry.component_version_id + entry.policy_version_id}>
                        <TableCell>{entry.component_version_id}</TableCell>
                        <TableCell>{entry.component_version_alias}</TableCell>
                        <TableCell>{entry.policy_id}</TableCell>
                        <TableCell>{entry.policy_name}</TableCell>
                        <TableCell>{entry.policy_version_id}</TableCell>
                        <TableCell>{entry.policy_version_alias}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
