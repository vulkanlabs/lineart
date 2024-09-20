"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { PolicyForm } from "@/components/policy-form";
import { PolicyTable } from "@/components/policy-table";
import { Button } from "@/components/ui/button";

export default function PoliciesPage({ policies }: { policies: any[] }) {
    const [showForm, setShowForm] = useState(false);
    const router = useRouter();

    return (
        <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Políticas</h1>
            </div>
            <div>
                {policies.length > 0 ? <PolicyTable policies={policies} /> : <EmptyPolicyTable />}
                <Button className="mt-4" onClick={() => setShowForm(true)}>Criar Política</Button>
                <Button className="mt-4" onClick={() => router.refresh()}>Refresh</Button>
                <PolicyForm display={showForm} closeFunc={() => setShowForm(false)} />
            </div>
        </main>
    );
}

function EmptyPolicyTable() {
    return (
        <div>
            <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm">
                <div className="flex flex-col items-center gap-1 text-center">
                    <h3 className="text-2xl font-bold tracking-tight">
                        Você não tem nenhuma política criada.
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Crie uma política para começar a tomar decisões.
                    </p>
                </div>
            </div>
        </div>
    );
}
