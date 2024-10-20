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

import { LinkIcon } from "lucide-react";
import Link from "next/link";

export type ComponentDependency = {
    component_name: string;
    component_id: string;
    component_version_id: string;
    component_version_alias: string;
    policy_id: string;
    policy_name: string;
    policy_version_id: string;
    policy_version_alias: string;
};

export function ComponentVersionDependenciesTable({ entries }: { entries: ComponentDependency[] }) {
    return (
        <Table>
            <TableCaption>Policies that use this Component.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>Component ID</TableHead>
                    <TableHead>Component Version</TableHead>
                    <TableHead>Policy ID</TableHead>
                    <TableHead>Policy Name</TableHead>
                    <TableHead>Policy Version</TableHead>
                    <TableHead>Version Tag</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {entries.map((entry) => (
                    <TableRow key={entry.component_version_id + entry.policy_version_id}>
                        <TableCell>
                            <ShortenedID id={entry.component_version_id} />
                        </TableCell>
                        <TableCell>{entry.component_version_alias}</TableCell>
                        <TableCell>
                            <ShortenedID id={entry.policy_id} />
                        </TableCell>
                        <TableCell>{entry.policy_name}</TableCell>
                        <TableCell>
                            <ShortenedID id={entry.policy_version_id} />
                        </TableCell>
                        <TableCell>{entry.policy_version_alias}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function PolicyVersionComponentDependenciesTable({
    entries,
}: {
    entries: ComponentDependency[];
}) {
    return (
        <Table>
            <TableCaption>Components used in this Policy Version.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>Component Name</TableHead>
                    <TableHead>Component Version</TableHead>
                    <TableHead>Component ID</TableHead>
                    <TableHead>Component Version ID</TableHead>
                    <TableHead>Link</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {entries.map((entry) => (
                    <TableRow key={entry.component_version_id + entry.policy_version_id}>
                        <TableCell>{entry.component_name}</TableCell>
                        <TableCell>{entry.component_version_alias}</TableCell>
                        <TableCell>
                            <ShortenedID id={entry.component_id} />
                        </TableCell>
                        <TableCell>
                            <ShortenedID id={entry.component_version_id} />
                        </TableCell>
                        <TableCell>
                            <Link href={`/components/`}>
                                <LinkIcon />
                            </Link>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
