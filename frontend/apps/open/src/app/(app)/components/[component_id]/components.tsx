"use client";
import { EnvironmentVariablesEditor } from "@vulkanlabs/base";
import { Card, CardTitle, CardHeader, CardContent } from "@vulkanlabs/base/ui";
import { Component, ConfigurationVariablesBase } from "@vulkanlabs/client-open";
import { useState } from "react";

export function EnvTab({ component }: { component: Component }) {
    // Prepare environment variables for the editor
    const [variables, setVariables] = useState<ConfigurationVariablesBase[]>([]);

    async function handleSave(updatedVariables: ConfigurationVariablesBase[]) {
        // TODO: Implement save logic (API call to update component variables)
        // await updateComponentEnvVars(component_id, updatedVariables);
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">Environment Variables</CardTitle>
            </CardHeader>
            <CardContent>
                <EnvironmentVariablesEditor variables={variables} onSave={handleSave} />
            </CardContent>
        </Card>
    );
}
