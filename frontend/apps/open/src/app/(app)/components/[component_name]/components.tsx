"use client";
import { EnvironmentVariablesEditor } from "@vulkanlabs/base";
import { Card, CardTitle, CardHeader, CardContent } from "@vulkanlabs/base/ui";
import { Component, ConfigurationVariablesBase } from "@vulkanlabs/client-open";
import { useState } from "react";
import { toast } from "sonner";

export function EnvTab({ component }: { component: Component }) {
    // Prepare environment variables for the editor
    const [variables, setVariables] = useState<ConfigurationVariablesBase[]>([]);

    async function handleSave(updatedVariables: ConfigurationVariablesBase[]) {
        try {
            // TODO: Implement save logic when component environment variables API is available
            // For now, show a message that this feature is not yet implemented
            toast.error("Component environment variables are not yet supported", {
                description: "This feature will be available in a future update.",
            });
        } catch (error) {
            toast.error("Failed to save environment variables", {
                description: error instanceof Error ? error.message : "An unknown error occurred",
            });
        }
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
