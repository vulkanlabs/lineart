"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useUser } from "@stackframe/stack";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CardContent } from "@mui/material";
import { fetchPolicyVersion } from "@/lib/api";

import { LaunchRunForm } from "./components";

export default function Page({ params }) {
    const user = useUser();
    const [createdRun, setCreatedRun] = useState(null);
    const [error, setError] = useState<Error>(null);

    const [inputSchema, setInputSchema] = useState<Map<string, string>>(null);
    const [configVariables, setConfigVariables] = useState<string[]>(null);

    useEffect(() => {
        const fetchPolicyVersionData = async () => {
            const policyVersion = await fetchPolicyVersion(user, params.policy_version_id);
            setConfigVariables(policyVersion.variables);

            const graphDefinition = await JSON.parse(policyVersion.graph_definition);
            const inputSchema = graphDefinition.input_node.metadata.schema;
            setInputSchema(inputSchema);
        };

        fetchPolicyVersionData().catch((error) => {
            console.log("Failed to fetch policy metadata", error);
        });
    }, []);

    return (
        <div className="flex flex-col p-8 gap-8">
            <h1 className="text-2xl font-bold tracking-tight">Launcher</h1>
            <div>
                <LaunchRunForm
                    user={user}
                    policy_version_id={params.policy_version_id}
                    setCreatedRun={setCreatedRun}
                    setError={setError}
                    defaultInputData={asInputData(inputSchema)}
                    defaultConfigVariables={asConfigMap(configVariables)}
                />
            </div>
            {createdRun && <RunCreatedCard createdRun={createdRun} />}
            {error && <RunCreationErrorCard error={error} />}
        </div>
    );
}

function asInputData(inputSchema: Map<string, string>) {
    if (!inputSchema) {
        return {};
    }

    const defaultValuePerType = Object.fromEntries([
        ["str", ""],
        ["int", 0],
        ["float", 0.0],
        ["boolean", false],
        ["dict", {}],
        ["list", []],
    ]);
    return Object.fromEntries(
        Object.entries(inputSchema).map(([key, value]) => {
            return [key, defaultValuePerType[value]];
        }),
    );
}

function asConfigMap(configVariables: string[]) {
    if (!configVariables) {
        return {};
    }

    return Object.fromEntries(configVariables.map((key) => [key, ""]));
}

function RunCreatedCard({ createdRun }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Launched run successfully</CardTitle>
                <CardDescription>
                    <Link href={`/policyVersions/${createdRun.policy_version_id}/runs/${createdRun.run_id}`}>
                        <Button className="bg-green-600 hover:bg-green-500">View Run</Button>
                    </Link>
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function RunCreationErrorCard({ error }) {
    console.log(error);
    return (
        <Card className="flex flex-col w-fit border-red-600 border-2">
            <CardHeader>
                <CardTitle>Failed to launch run</CardTitle>
                <CardDescription>
                    Launch failed with error: <br />
                </CardDescription>
            </CardHeader>
            <CardContent>
                <pre className="text-wrap">{error.message}</pre>
            </CardContent>
        </Card>
    );
}
