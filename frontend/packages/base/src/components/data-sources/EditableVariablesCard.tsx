"use client";

import { useState, useEffect, useCallback } from "react";
import { FileIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Separator } from "@vulkanlabs/base/ui";
import { EnvironmentVariablesEditor } from "../..";
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";

interface EditableVariablesCardProps {
    dataSource: DataSource;
    projectId?: string;
    fetchDataSourceEnvVars: (
        dataSourceId: string,
        projectId?: string,
    ) => Promise<DataSourceEnvVarBase[]>;
    setDataSourceEnvVars: (
        dataSourceId: string,
        variables: DataSourceEnvVarBase[],
        projectId?: string,
    ) => Promise<void>;
}

export function EditableVariablesCard({
    dataSource,
    projectId,
    fetchDataSourceEnvVars,
    setDataSourceEnvVars,
}: EditableVariablesCardProps) {
    const runtimeParams = dataSource.runtime_params || [];
    const [variables, setVariables] = useState<DataSourceEnvVarBase[]>([]);

    const fetchVariables = useCallback(async () => {
        try {
            const envVars = await fetchDataSourceEnvVars(dataSource.data_source_id, projectId);
            setVariables(envVars);
        } catch (error) {
            console.error("Failed to fetch environment variables:", error);
            setVariables([]);
        }
    }, [dataSource.data_source_id, fetchDataSourceEnvVars]);

    useEffect(() => {
        fetchVariables();
    }, [fetchVariables]);

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <FileIcon className="h-5 w-5" />
                        Variables
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                <div>
                    <h4 className="text-sm font-medium mb-3">Runtime Parameters</h4>
                    <p className="text-xs text-muted-foreground mb-3">
                        These parameters are configured in the workflows that use the data source.
                    </p>
                    {runtimeParams.length > 0 ? (
                        <div className="space-y-2">
                            {runtimeParams.map((param, index) => (
                                <div
                                    key={index}
                                    className="flex items-center justify-between p-2 bg-muted/30 rounded 
                                        border-l-2 border-blue-500"
                                >
                                    <span className="text-sm font-medium">{param}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground">
                            No runtime parameters configured.
                        </p>
                    )}
                </div>

                <Separator />

                <EnvironmentVariablesEditor
                    variables={variables}
                    requiredVariableNames={dataSource.variables || []}
                    onSave={async (updatedVariables: DataSourceEnvVarBase[]) => {
                        await setDataSourceEnvVars(
                            dataSource.data_source_id,
                            updatedVariables,
                            projectId,
                        );
                    }}
                />
            </CardContent>
        </Card>
    );
}
