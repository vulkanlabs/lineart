"use client";

import { useState, useEffect } from "react";
import { Shield, Save, X } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";
import { Button, Card, CardContent, CardHeader, CardTitle, Separator } from "../ui";
import { toast } from "sonner";

import { AuthMethodSelector, AuthMethod } from "./AuthMethodSelector";
import { BasicAuthConfig } from "./BasicAuthConfig";
import { BearerAuthConfig, GrantType } from "./BearerAuthConfig";

interface AuthenticationConfigCardProps {
    dataSource: DataSource;
    projectId?: string;
    updateDataSource: (
        dataSourceId: string,
        updates: Partial<DataSource>,
        projectId?: string,
    ) => Promise<DataSource>;
    fetchDataSourceEnvVars: (
        dataSourceId: string,
        projectId?: string,
    ) => Promise<DataSourceEnvVarBase[]>;
    setDataSourceEnvVars: (
        dataSourceId: string,
        variables: DataSourceEnvVarBase[],
        projectId?: string,
    ) => Promise<void>;
    disabled?: boolean;
}

export function AuthenticationConfigCard({
    dataSource,
    projectId,
    updateDataSource,
    fetchDataSourceEnvVars,
    setDataSourceEnvVars,
    disabled = false,
}: AuthenticationConfigCardProps) {
    const router = useRouter();
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const sourceWithAuth = dataSource.source as any;

    const getCurrentAuthMethod = (): AuthMethod => {
        if (!sourceWithAuth.auth) return "none";
        return sourceWithAuth.auth.method as AuthMethod;
    };

    const [authMethod, setAuthMethod] = useState<AuthMethod>(getCurrentAuthMethod());

    const [clientId, setClientId] = useState("");
    const [clientSecret, setClientSecret] = useState("");

    const [tokenUrl, setTokenUrl] = useState(sourceWithAuth.auth?.token_url || "");
    const [grantType, setGrantType] = useState<GrantType>(
        (sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials"
    );
    const [scope, setScope] = useState(sourceWithAuth.auth?.scope || "");

    useEffect(() => {
        const loadCredentials = async () => {
            try {
                const envVars = await fetchDataSourceEnvVars(dataSource.data_source_id, projectId);
                const clientIdVar = envVars.find((v) => v.name === "CLIENT_ID");
                const clientSecretVar = envVars.find((v) => v.name === "CLIENT_SECRET");

                if (clientIdVar) setClientId(String(clientIdVar.value || ""));
                if (clientSecretVar) setClientSecret(String(clientSecretVar.value || ""));
            } catch (error) {
                console.error("Failed to load credentials:", error);
            }
        };

        if (sourceWithAuth.auth) loadCredentials();
    }, [dataSource, projectId, fetchDataSourceEnvVars]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const sourceUpdates: any = {
                ...dataSource.source,
            };

            if (authMethod === "none") {
                // Remove auth
                delete sourceUpdates.auth;
            } else if (authMethod === "basic") {
                // Basic auth
                sourceUpdates.auth = {
                    method: "basic",
                };
            } else if (authMethod === "bearer") {
                // Bearer/OAuth auth
                if (!tokenUrl) {
                    toast.error("Token URL is required for Bearer authentication");
                    setIsSaving(false);
                    return;
                }

                sourceUpdates.auth = {
                    method: "bearer",
                    token_url: tokenUrl,
                    grant_type: grantType,
                    scope: scope || undefined,
                };
            }

            // Update DataSource
            await updateDataSource(
                dataSource.data_source_id,
                { source: sourceUpdates },
                projectId
            );

            // Update credentials (CLIENT_ID, CLIENT_SECRET) if auth is configured
            if (authMethod !== "none") {
                const credentials: DataSourceEnvVarBase[] = [
                    { name: "CLIENT_ID", value: clientId },
                    { name: "CLIENT_SECRET", value: clientSecret },
                ];

                await setDataSourceEnvVars(
                    dataSource.data_source_id,
                    credentials,
                    projectId
                );
            }

            toast.success("Authentication configuration updated successfully");
            setIsEditing(false);
            router.refresh();
        } catch (error: any) {
            console.error("Failed to update authentication:", error);
            toast.error(error.message || "Failed to update authentication");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        // Reset to current values
        setAuthMethod(getCurrentAuthMethod());
        setTokenUrl(sourceWithAuth.auth?.token_url || "");
        setGrantType((sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials");
        setScope(sourceWithAuth.auth?.scope || "");
        setIsEditing(false);
    };

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Authentication
                    </CardTitle>
                    {!isEditing && !disabled ? (
                        <Button onClick={() => setIsEditing(true)} variant="outline" size="sm">
                            Edit
                        </Button>
                    ) : isEditing ? (
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleCancel}
                                disabled={isSaving}
                            >
                                <X className="h-4 w-4 mr-1" />
                                Cancel
                            </Button>
                            <Button size="sm" onClick={handleSave} disabled={isSaving}>
                                <Save className="h-4 w-4 mr-1" />
                                {isSaving ? "Saving..." : "Save"}
                            </Button>
                        </div>
                    ) : null}
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    <AuthMethodSelector
                        value={authMethod}
                        onChange={setAuthMethod}
                        disabled={!isEditing || disabled}
                    />

                    {authMethod !== "none" && (
                        <>
                            <Separator />

                            {authMethod === "basic" && (
                                <BasicAuthConfig
                                    clientId={clientId}
                                    clientSecret={clientSecret}
                                    onClientIdChange={setClientId}
                                    onClientSecretChange={setClientSecret}
                                    disabled={!isEditing || disabled}
                                />
                            )}

                            {authMethod === "bearer" && (
                                <BearerAuthConfig
                                    tokenUrl={tokenUrl}
                                    grantType={grantType}
                                    scope={scope}
                                    clientId={clientId}
                                    clientSecret={clientSecret}
                                    onTokenUrlChange={setTokenUrl}
                                    onGrantTypeChange={setGrantType}
                                    onScopeChange={setScope}
                                    onClientIdChange={setClientId}
                                    onClientSecretChange={setClientSecret}
                                    disabled={!isEditing || disabled}
                                />
                            )}
                        </>
                    )}

                    {disabled && (
                        <p className="text-xs text-muted-foreground">
                            Authentication cannot be modified for published data sources.
                        </p>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
