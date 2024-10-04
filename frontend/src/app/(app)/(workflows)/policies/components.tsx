"use client";

import React, { useState, useEffect } from "react";
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
import { Button } from "@/components/ui/button";
import { PolicyForm } from "@/components/policy-form";

export default function PoliciesPage({ policies }: { policies: any[] }) {
    const [showForm, setShowForm] = useState(false);
    const router = useRouter();

    return (
        <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Policies</h1>
            </div>
            <div>
                {policies.length > 0 ? <PolicyTable policies={policies} /> : <EmptyPolicyTable />}
                {/* <Button className="mt-4" onClick={() => setShowForm(true)}>
                    Create Policy
                </Button> */}
                <Button className="mt-4" onClick={() => router.refresh()}>
                    Refresh
                </Button>
                {/* <PolicyForm display={showForm} closeFunc={() => setShowForm(false)} /> */}
            </div>
        </main>
    );
}

export function PolicyTable({ policies }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Your policies.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Active Version</TableHead>
                    <TableHead>Last Updated At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {policies.map((policy) => (
                    <TableRow
                        key={policy.policy_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/policies/${policy.policy_id}/versions`)}
                    >
                        <TableCell>{policy.policy_id}</TableCell>
                        <TableCell>{policy.name}</TableCell>
                        <TableCell>
                            {policy.description.length > 0 ? policy.description : "-"}
                        </TableCell>
                        <TableCell>
                            {policy.active_policy_version_id !== null
                                ? policy.active_policy_version_id
                                : "-"}
                        </TableCell>
                        <TableCell>{policy.last_updated_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

function EmptyPolicyTable() {
    return (
        <div>
            <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm">
                <div className="flex flex-col items-center gap-1 text-center">
                    <h3 className="text-2xl font-bold tracking-tight">You have no policies yet.</h3>
                    <p className="text-sm text-muted-foreground">
                        Create a Policy to start making decisions.
                    </p>
                </div>
            </div>
        </div>
    );
}
