"use client";

import React, { useState, useEffect } from "react";
import { PolicyForm } from "@/components/policy-form";
import { PolicyTable } from "@/components/policy-table";
import { Button } from "@/components/ui/button";
import { fetchPolicies } from "@/lib/policies";

export default function PolicyPageBody() {
    const [policies, setPolicies] = useState([]);
    const refreshTime = 3000;
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    useEffect(() => {
        const comInterval = setInterval(() => {
            fetchPolicies(baseUrl).then((data) => setPolicies(data));
        }, refreshTime);
        return () => clearInterval(comInterval);
    }, []);

    return (
        <div>
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Políticas</h1>
            </div>
            <PolicyPageContent policies={policies} />
        </div>
    );
}

function PolicyPageContent({ policies }) {
    const [showForm, setShowForm] = useState(false);

    return (
        <div>
            <Button className="mt-4" onClick={() => setShowForm(true)}>Criar Política</Button>
            {policies.length > 0 ? <PolicyTable policies={policies} /> : <EmptyPolicyTable />}
            <PolicyForm display={showForm} closeFunc={() => setShowForm(false)} />
        </div>
    );
}

function EmptyPolicyTable() {
    return (
        <div>
            <div
                className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm"
            >
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