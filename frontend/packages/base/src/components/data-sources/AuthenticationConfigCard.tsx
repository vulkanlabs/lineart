"use client";

import { useState, useEffect } from "react";
import { Save, X, Shield, Edit2 } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";
import { Button, Input, Label, Separator, RadioGroup, RadioGroupItem, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui";

type AuthMethod = "none" | "basic" | "bearer";
type GrantType = "client_credentials" | "password" | "implicit";

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
    const [isEditingCredentials, setIsEditingCredentials] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const sourceWithAuth = dataSource.source as any;
    const isDraft = dataSource.status === "DRAFT";

    const getCurrentAuthMethod = (): AuthMethod => {
        if (!sourceWithAuth.auth) return "none";
        return sourceWithAuth.auth.method as AuthMethod;
    };

    // Auth state
    const [authMethod, setAuthMethod] = useState<AuthMethod>(getCurrentAuthMethod());
    const [clientId, setClientId] = useState("");
    const [clientIdInput, setClientIdInput] = useState("");
    const [hasClientId, setHasClientId] = useState(false);
    const [clientSecret, setClientSecret] = useState("");
    const [clientSecretInput, setClientSecretInput] = useState("");
    const [hasSecret, setHasSecret] = useState(false);
    const [tokenUrl, setTokenUrl] = useState(sourceWithAuth.auth?.token_url || "");
    const [grantType, setGrantType] = useState<GrantType>(
        (sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials"
    );
    const [scope, setScope] = useState(sourceWithAuth.auth?.scope || "");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [hasPassword, setHasPassword] = useState(false);

    // Validation errors
    const [tokenUrlError, setTokenUrlError] = useState("");
    const [credentialsError, setCredentialsError] = useState("");
    const [passwordGrantError, setPasswordGrantError] = useState("");

    // Load credentials from env vars
    useEffect(() => {
        const loadCredentials = async () => {
            try {
                const envVars = await fetchDataSourceEnvVars(dataSource.data_source_id, projectId);
                const clientIdVar = envVars.find((v) => v.name === "CLIENT_ID");
                const clientSecretVar = envVars.find((v) => v.name === "CLIENT_SECRET");
                const usernameVar = envVars.find((v) => v.name === "USERNAME");
                const passwordVar = envVars.find((v) => v.name === "PASSWORD");

                if (clientIdVar) {
                    setClientId(String(clientIdVar.value || ""));
                    setHasClientId(true);
                } else {
                    setHasClientId(false);
                }

                if (clientSecretVar) {
                    setClientSecret("");
                    setHasSecret(true);
                } else {
                    setHasSecret(false);
                }

                if (usernameVar)
                    setUsername(String(usernameVar.value || ""));

                if (passwordVar) {
                    setPassword("");
                    setHasPassword(true);
                } else {
                    setHasPassword(false);
                }
            } catch (error) {
                console.error("Failed to load credentials:", error);
            }
        };

        loadCredentials();
    }, [dataSource.data_source_id, projectId, fetchDataSourceEnvVars]);

    // Auto-enable credential editing when auth method changes and no credentials exist
    useEffect(() => {
        if (isEditing && authMethod !== "none" && !hasClientId && !hasSecret) {
            setIsEditingCredentials(true);
        }
    }, [authMethod, isEditing, hasClientId, hasSecret]);

    const handleSave = async () => {
        // Clear previous errors
        setTokenUrlError("");
        setCredentialsError("");
        setPasswordGrantError("");

        // Validate required fields for Bearer auth
        if (authMethod === "bearer") {
            if (!tokenUrl || tokenUrl.trim() === "") {
                setTokenUrlError("Token URL is required for Bearer authentication");
                return;
            }

            // Validate password grant type specific fields, only if not already saved
            if (grantType === "password") {
                const needsUsername = !username || !username.trim();
                const needsPassword = !password || (!password.trim() && !hasPassword);

                if (needsUsername || needsPassword) {
                    setPasswordGrantError("Username and Password are required for Password grant type");
                    return;
                }
            }
        }

        // Validate credentials if auth is enabled and we're editing credentials
        if (authMethod !== "none" && (isEditingCredentials || !hasClientId)) {
            // For credential editing mode, use inputs; otherwise use stored values
            const finalClientId = isEditingCredentials ? clientIdInput : (clientIdInput || clientId);
            const finalSecret = isEditingCredentials ? clientSecretInput : (clientSecretInput || clientSecret);

            if (!finalClientId || !finalClientId.trim() || !finalSecret || !finalSecret.trim()) {
                setCredentialsError("Both Client ID and Client Secret are required");
                return;
            }
        }

        setIsSaving(true);
        try {

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

            await updateDataSource(
                dataSource.data_source_id,
                {
                    name: dataSource.name,
                    source: sourceUpdates,
                    caching: dataSource.caching,
                },
                projectId
            );

            // Update credentials if auth is configured and credentials were edited
            if (authMethod !== "none") {
                const credentials: DataSourceEnvVarBase[] = [];

                if (isEditingCredentials || !hasClientId) {
                    const finalClientId = clientIdInput || clientId;
                    const finalSecret = clientSecretInput || clientSecret;
                    credentials.push({ name: "CLIENT_ID", value: finalClientId });
                    credentials.push({ name: "CLIENT_SECRET", value: finalSecret });

                    // Update stored credential state
                    setClientId(finalClientId);
                    setHasClientId(true);
                    setClientSecret(finalSecret);
                    setHasSecret(true);
                }

                if (grantType === "password" && username && password) {
                    credentials.push({ name: "USERNAME", value: username });
                    credentials.push({ name: "PASSWORD", value: password });
                }

                // Only call API if we have credentials to save
                if (credentials.length > 0) {
                    await setDataSourceEnvVars(
                        dataSource.data_source_id,
                        credentials,
                        projectId
                    );
                }
            }

            setIsEditing(false);
            setIsEditingCredentials(false);
            setClientIdInput("");
            setClientSecretInput("");
            router.refresh();
        } catch (error: any) {
            console.error("Failed to save authentication:", error);
            setCredentialsError(error.message || "Failed to save authentication configuration");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setAuthMethod(getCurrentAuthMethod());
        setTokenUrl(sourceWithAuth.auth?.token_url || "");
        setGrantType((sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials");
        setScope(sourceWithAuth.auth?.scope || "");
        setClientIdInput("");
        setClientSecretInput("");
        setIsEditing(false);
        setIsEditingCredentials(false);
        setTokenUrlError("");
        setCredentialsError("");
        setPasswordGrantError("");
    };

    const handleEditCredentials = () => {
        setIsEditingCredentials(true);
        // Pre-populate inputs with current values for editing
        setClientIdInput(clientId);
        setClientSecretInput("");
    };

    const handleCancelCredentials = () => {
        setIsEditingCredentials(false);
        setClientIdInput("");
        setClientSecretInput("");
        setCredentialsError("");
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold md:text-2xl">Authentication</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Configure authentication for external API requests
                    </p>
                </div>
                {!isEditing ? (
                    <Button onClick={() => setIsEditing(true)} disabled={!isDraft}>
                        <Shield className="h-4 w-4 mr-2" />
                        Edit
                    </Button>
                ) : (
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving}>
                            <Save className="h-4 w-4 mr-2" />
                            {isSaving ? "Saving..." : "Save"}
                        </Button>
                    </div>
                )}
            </div>

            <Separator />

            <div className="space-y-6">
                <div className="space-y-3">
                    <Label className="text-sm font-medium">Authentication Method</Label>

                    <RadioGroup
                        value={authMethod}
                        onValueChange={(value) => isEditing && setAuthMethod(value as AuthMethod)}
                        disabled={!isEditing || disabled}
                        className="space-y-2"
                    >
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="none" id="auth-none" disabled={!isEditing || disabled} />
                            <Label htmlFor="auth-none" className="text-sm font-normal cursor-pointer">
                                None
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="basic" id="auth-basic" disabled={!isEditing || disabled} />
                            <Label htmlFor="auth-basic" className="text-sm font-normal cursor-pointer">
                                Basic Authentication
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="bearer" id="auth-bearer" disabled={!isEditing || disabled} />
                            <Label htmlFor="auth-bearer" className="text-sm font-normal cursor-pointer">
                                Bearer Token / OAuth
                            </Label>
                        </div>
                    </RadioGroup>
                </div>

                {authMethod !== "none" && (
                    <>
                        <Separator className="my-6" />

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-medium">Credentials</h4>
                                {isEditing && !isEditingCredentials && (hasClientId || hasSecret) && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleEditCredentials}
                                        disabled={disabled}
                                    >
                                        <Edit2 className="h-3 w-3 mr-1" />
                                        Edit Credentials
                                    </Button>
                                )}
                                {isEditingCredentials && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleCancelCredentials}
                                    >
                                        <X className="h-3 w-3 mr-1" />
                                        Cancel
                                    </Button>
                                )}
                            </div>

                            {credentialsError && (
                                <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
                                    {credentialsError}
                                </div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="client-id" className="text-sm">
                                    Client ID
                                </Label>
                                <Input
                                    id="client-id"
                                    value={isEditingCredentials ? clientIdInput : (clientId || "")}
                                    onChange={(e) => {
                                        setClientIdInput(e.target.value);
                                        if (credentialsError) setCredentialsError("");
                                    }}
                                    disabled={!isEditing || !isEditingCredentials || disabled}
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
                                    value={isEditingCredentials ? clientSecretInput : (hasSecret ? "••••••••" : "")}
                                    onChange={(e) => {
                                        setClientSecretInput(e.target.value);
                                        if (credentialsError) setCredentialsError("");
                                    }}
                                    disabled={!isEditing || !isEditingCredentials || disabled}
                                    placeholder={isEditingCredentials ? "Enter new client secret" : ""}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Secret is encrypted and never exposed in API responses.
                                </p>
                            </div>
                        </div>
                    </>
                )}

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
                                    onChange={(e) => {
                                        setTokenUrl(e.target.value);
                                        if (tokenUrlError) setTokenUrlError("");
                                    }}
                                    disabled={!isEditing || disabled}
                                    placeholder="https://auth.example.com/oauth/token"
                                    className={tokenUrlError ? "border-red-500" : ""}
                                />
                                {tokenUrlError && (
                                    <p className="text-sm text-red-600">{tokenUrlError}</p>
                                )}
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
                                        <SelectItem value="client_credentials">Client Credentials</SelectItem>
                                        <SelectItem value="password">Password</SelectItem>
                                        <SelectItem value="implicit">Implicit</SelectItem>
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

                            {grantType === "password" && (
                                <>
                                    <Separator className="my-4" />
                                    <h5 className="text-sm font-medium">Password Grant Credentials</h5>

                                    {passwordGrantError && (
                                        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
                                            {passwordGrantError}
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <Label htmlFor="username" className="text-sm">
                                            Username <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="username"
                                            value={username}
                                            onChange={(e) => {
                                                setUsername(e.target.value);
                                                if (passwordGrantError) setPasswordGrantError("");
                                            }}
                                            disabled={!isEditing || disabled}
                                            placeholder="Enter username"
                                            className={passwordGrantError ? "border-red-500" : ""}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="password" className="text-sm">
                                            Password <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="password"
                                            type="password"
                                            value={password || (hasPassword ? "••••••••" : "")}
                                            onChange={(e) => {
                                                setPassword(e.target.value);
                                                if (passwordGrantError) setPasswordGrantError("");
                                            }}
                                            disabled={!isEditing || disabled}
                                            placeholder={hasPassword ? "••••••••" : "Enter password"}
                                            className={passwordGrantError ? "border-red-500" : ""}
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            {hasPassword
                                                ? "Password is encrypted and stored securely"
                                                : "Used for Password Credentials grant"}
                                        </p>
                                    </div>
                                </>
                            )}
                        </div>
                    </>
                )}

                {!isDraft && (
                    <p className="text-xs text-muted-foreground mt-4">
                        Authentication cannot be modified for published data sources.
                    </p>
                )}
            </div>
        </div>
    );
}
