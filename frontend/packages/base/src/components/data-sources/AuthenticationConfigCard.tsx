"use client";

import { useState, useEffect } from "react";
import { Save, X } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";
import {
    Button,
    Input,
    Label,
    Separator,
    RadioGroup,
    RadioGroupItem,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "../ui";
import { toast } from "sonner";

type AuthMethod = "none" | "basic" | "bearer";
type GrantType = "client_credentials" | "password" | "authorization_code";

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
    const [clientSecretInput, setClientSecretInput] = useState("");
    const [hasSecret, setHasSecret] = useState(false);
    const [tokenUrl, setTokenUrl] = useState(sourceWithAuth.auth?.token_url || "");
    const [grantType, setGrantType] = useState<GrantType>(
        (sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials",
    );
    const [scope, setScope] = useState(sourceWithAuth.auth?.scope || "");

    // Load credentials from env vars
    useEffect(() => {
        const loadCredentials = async () => {
            try {
                const envVars = await fetchDataSourceEnvVars(dataSource.data_source_id, projectId);
                const clientIdVar = envVars.find((v) => v.name === "CLIENT_ID");
                const clientSecretVar = envVars.find((v) => v.name === "CLIENT_SECRET");

                if (clientIdVar) setClientId(String(clientIdVar.value || ""));
                if (clientSecretVar) {
                    setClientSecret(String(clientSecretVar.value || ""));
                    setHasSecret(!!clientSecretVar.value);
                }
            } catch (error) {
                console.error("Failed to load credentials:", error);
            }
        };

        if (sourceWithAuth.auth) loadCredentials();
    }, [dataSource, projectId, fetchDataSourceEnvVars, sourceWithAuth.auth]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            // Validate required fields for Bearer auth
            if (authMethod === "bearer" && !tokenUrl) {
                toast.error("Token URL is required for Bearer authentication");
                setIsSaving(false);
                return;
            }

            // Build updated source with auth configuration
            const sourceUpdates: any = {
                ...dataSource.source,
            };

            if (authMethod === "none") {
                delete sourceUpdates.auth;
            } else if (authMethod === "basic") {
                sourceUpdates.auth = {
                    method: "basic",
                };
            } else if (authMethod === "bearer") {
                sourceUpdates.auth = {
                    method: "bearer",
                    token_url: tokenUrl,
                    grant_type: grantType,
                    scope: scope || undefined,
                };
            }

            const dataSourceSpec: any = {
                name: dataSource.name,
                source: sourceUpdates,
                caching: dataSource.caching,
                description: dataSource.description,
                metadata: dataSource.metadata,
            };

            // Update data source with auth configuration
            await updateDataSource(dataSource.data_source_id, dataSourceSpec, projectId);

            // Update credentials if auth is configured
            if (authMethod !== "none") {
                const finalSecret = clientSecretInput || clientSecret;

                // Validate credentials
                if (!clientId || !finalSecret) {
                    toast.error("Client ID and Client Secret are required");
                    setIsSaving(false);
                    return;
                }

                const credentials: DataSourceEnvVarBase[] = [
                    { name: "CLIENT_ID", value: clientId },
                    { name: "CLIENT_SECRET", value: finalSecret },
                ];

                await setDataSourceEnvVars(dataSource.data_source_id, credentials, projectId);
            }

            toast.success("Authentication configuration saved");
            setIsEditing(false);
            setClientSecretInput("");
            router.refresh();
        } catch (error: any) {
            console.error("Failed to save authentication:", error);
            toast.error(error.message || "Failed to save authentication");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setAuthMethod(getCurrentAuthMethod());
        setTokenUrl(sourceWithAuth.auth?.token_url || "");
        setGrantType((sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials");
        setScope(sourceWithAuth.auth?.scope || "");
        setClientSecretInput("");
        setIsEditing(false);
    };

    const handleSecretBlur = () => {
        if (clientSecretInput) {
            setHasSecret(true);
            setClientSecret(clientSecretInput);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-base font-semibold mb-3">Authentication</h3>
                <p className="text-xs text-muted-foreground mb-4">
                    Configure authentication for external API requests. Credentials are encrypted at
                    rest using AES-256-GCM.
                </p>

                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Authentication Method</Label>

                        {!disabled && (
                            <div className="flex gap-2">
                                {!isEditing ? (
                                    <Button
                                        onClick={() => setIsEditing(true)}
                                        variant="outline"
                                        size="sm"
                                    >
                                        Edit
                                    </Button>
                                ) : (
                                    <>
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
                                    </>
                                )}
                            </div>
                        )}
                    </div>

                    <RadioGroup
                        value={authMethod}
                        onValueChange={(value) => isEditing && setAuthMethod(value as AuthMethod)}
                        disabled={!isEditing || disabled}
                        className="space-y-2"
                    >
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem
                                value="none"
                                id="auth-none"
                                disabled={!isEditing || disabled}
                            />
                            <Label
                                htmlFor="auth-none"
                                className="text-sm font-normal cursor-pointer"
                            >
                                None
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem
                                value="basic"
                                id="auth-basic"
                                disabled={!isEditing || disabled}
                            />
                            <Label
                                htmlFor="auth-basic"
                                className="text-sm font-normal cursor-pointer"
                            >
                                Basic Authentication (Base64 encoded credentials)
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem
                                value="bearer"
                                id="auth-bearer"
                                disabled={!isEditing || disabled}
                            />
                            <Label
                                htmlFor="auth-bearer"
                                className="text-sm font-normal cursor-pointer"
                            >
                                Bearer Token / OAuth
                            </Label>
                        </div>
                    </RadioGroup>
                </div>

                {authMethod !== "none" && (
                    <>
                        <Separator className="my-6" />

                        <div className="space-y-4">
                            <h4 className="text-sm font-medium">Credentials</h4>

                            <div className="space-y-2">
                                <Label htmlFor="client-id" className="text-sm">
                                    Client ID
                                </Label>
                                <Input
                                    id="client-id"
                                    value={clientId}
                                    onChange={(e) => setClientId(e.target.value)}
                                    disabled={!isEditing || disabled}
                                    placeholder="Enter client ID"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="client-secret" className="text-sm">
                                    Client Secret
                                </Label>
                                <Input
                                    id="client-secret"
                                    type="password"
                                    value={clientSecretInput}
                                    onChange={(e) => setClientSecretInput(e.target.value)}
                                    onBlur={handleSecretBlur}
                                    disabled={!isEditing || disabled}
                                    placeholder={hasSecret ? "••••••••" : "Enter client secret"}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Secret is encrypted and never exposed in API responses.
                                </p>
                            </div>
                        </div>
                    </>
                )}

                {/* Bearer-specific configuration */}
                {authMethod === "bearer" && (
                    <>
                        <Separator className="my-6" />

                        <div className="space-y-4">
                            <h4 className="text-sm font-medium">OAuth Configuration</h4>

                            <div className="space-y-2">
                                <Label htmlFor="token-url" className="text-sm">
                                    Token URL <span className="text-red-500">*</span>
                                </Label>
                                <Input
                                    id="token-url"
                                    value={tokenUrl}
                                    onChange={(e) => setTokenUrl(e.target.value)}
                                    disabled={!isEditing || disabled}
                                    placeholder="https://auth.example.com/oauth/token"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="grant-type" className="text-sm">
                                    Grant Type
                                </Label>
                                <Select
                                    value={grantType}
                                    onValueChange={(value) => setGrantType(value as GrantType)}
                                    disabled={!isEditing || disabled}
                                >
                                    <SelectTrigger id="grant-type">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="client_credentials">
                                            Client Credentials
                                        </SelectItem>
                                        <SelectItem value="password">Password</SelectItem>
                                        <SelectItem value="authorization_code">
                                            Authorization Code
                                        </SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="scope" className="text-sm">
                                    Scope (Optional)
                                </Label>
                                <Input
                                    id="scope"
                                    value={scope}
                                    onChange={(e) => setScope(e.target.value)}
                                    disabled={!isEditing || disabled}
                                    placeholder="read write"
                                />
                            </div>

                            <p className="text-xs text-muted-foreground">
                                Tokens are cached in Redis with TTL based on token expiration for
                                optimal performance.
                            </p>
                        </div>
                    </>
                )}

                {disabled && (
                    <p className="text-xs text-muted-foreground mt-4">
                        Authentication cannot be modified for published data sources.
                    </p>
                )}
            </div>
        </div>
    );
}
