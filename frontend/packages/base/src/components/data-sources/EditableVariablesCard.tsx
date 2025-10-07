"use client";

import { useState, useEffect, useCallback } from "react";

import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";

import { Separator } from "../ui";
import { EnvironmentVariablesEditor } from "../..";

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
        <div className="space-y-6">
            <div>
                <h3 className="text-base font-semibold mb-3">Runtime Parameters</h3>
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

            <div>
                <h3 className="text-base font-semibold mb-3">Environment Variables</h3>
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
            </div>
        </div>
    );
}
