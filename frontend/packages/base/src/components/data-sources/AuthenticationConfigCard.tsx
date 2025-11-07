"use client";

import { useState, useEffect } from "react";
import { Save, X, Shield, Edit2 } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource } from "@vulkanlabs/client-open";
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
import { ConfirmCredentialUpdateDialog } from "./ConfirmCredentialUpdateDialog";

type AuthMethod = "none" | "basic" | "bearer";
type GrantType = "client_credentials" | "password" | "implicit";

interface AuthenticationConfigCardProps {
    dataSource: DataSource;
    projectId?: string;
    fetchDataSource: (dataSourceId: string, projectId?: string) => Promise<DataSource>;
    updateDataSource: (
        dataSourceId: string,
        updates: Partial<DataSource>,
        projectId?: string,
    ) => Promise<DataSource>;
    fetchDataSourceCredentials: (dataSourceId: string, projectId?: string) => Promise<any[]>;
    setDataSourceCredentials: (
        dataSourceId: string,
        credentials: Array<{ credential_type: string; value: string }>,
        projectId?: string,
    ) => Promise<any>;
    disabled?: boolean;
}

export function AuthenticationConfigCard({
    dataSource,
    projectId,
    fetchDataSource,
    updateDataSource,
    fetchDataSourceCredentials,
    setDataSourceCredentials,
    disabled = false,
}: AuthenticationConfigCardProps) {
    const router = useRouter();
    const [isEditing, setIsEditing] = useState(false);
    const [isEditingCredentials, setIsEditingCredentials] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);

    const sourceWithAuth = dataSource.source as any;
    const isPublished = dataSource.status === "PUBLISHED";

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
        (sourceWithAuth.auth?.grant_type as GrantType) || "client_credentials",
    );
    const [scope, setScope] = useState(sourceWithAuth.auth?.scope || "");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [hasPassword, setHasPassword] = useState(false);

    // Validation errors
    const [tokenUrlError, setTokenUrlError] = useState("");
    const [credentialsError, setCredentialsError] = useState("");
    const [passwordGrantError, setPasswordGrantError] = useState("");

    // Load credentials from dedicated credentials table
    useEffect(() => {
        const loadCredentials = async () => {
            try {
                const credentials = await fetchDataSourceCredentials(
                    dataSource.data_source_id,
                    projectId,
                );
                const clientIdCred = credentials.find((c) => c.credential_type === "CLIENT_ID");
                const clientSecretCred = credentials.find(
                    (c) => c.credential_type === "CLIENT_SECRET",
                );
                const usernameCred = credentials.find((c) => c.credential_type === "USERNAME");
                const passwordCred = credentials.find((c) => c.credential_type === "PASSWORD");

                if (clientIdCred) {
                    setClientId(String(clientIdCred.value || ""));
                    setHasClientId(true);
                } else {
                    setHasClientId(false);
                }

                if (clientSecretCred) {
                    setClientSecret("");
                    setHasSecret(true);
                } else {
                    setHasSecret(false);
                }

                if (usernameCred) setUsername(String(usernameCred.value || ""));

                if (passwordCred) {
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
    }, [dataSource.data_source_id, projectId, fetchDataSourceCredentials]);

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
                    setPasswordGrantError(
                        "Username and Password are required for Password grant type",
                    );
                    return;
                }
            }
        }

        // Validate credentials if auth is enabled and we're editing credentials
        if (authMethod !== "none" && (isEditingCredentials || !hasClientId)) {
            // For credential editing mode, use inputs; otherwise use stored values
            const finalClientId = isEditingCredentials ? clientIdInput : clientIdInput || clientId;
            const finalSecret = isEditingCredentials
                ? clientSecretInput
                : clientSecretInput || clientSecret;

            if (!finalClientId || !finalClientId.trim() || !finalSecret || !finalSecret.trim()) {
                setCredentialsError("Both Client ID and Client Secret are required");
                return;
            }
        }

        if (isPublished && isEditingCredentials) {
            setShowConfirmDialog(true);
            return;
        }

        await performSave();
    };

    const performSave = async () => {
        setIsSaving(true);
        setShowConfirmDialog(false);
        try {
            // For published data sources editing only credentials, skip updateDataSource
            // and only update credentials via the dedicated credentials endpoint
            if (!(isPublished && isEditingCredentials)) {
                // Fetch latest dataSource from server to avoid overwriting other changes
                const latestDataSource = await fetchDataSource(
                    dataSource.data_source_id,
                    projectId,
                );

                // Build updated source with auth configuration from latest state
                const sourceUpdates: any = {
                    ...latestDataSource.source,
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
                        name: latestDataSource.name,
                        source: sourceUpdates,
                        caching: latestDataSource.caching,
                    },
                    projectId,
                );
            }

            // Update credentials if auth is configured and credentials were edited
            if (authMethod !== "none") {
                const credentials: Array<{ credential_type: string; value: string }> = [];

                if (isEditingCredentials || !hasClientId) {
                    const finalClientId = clientIdInput || clientId;
                    const finalSecret = clientSecretInput || clientSecret;
                    credentials.push({ credential_type: "CLIENT_ID", value: finalClientId });
                    credentials.push({ credential_type: "CLIENT_SECRET", value: finalSecret });

                    // Update stored credential state
                    setClientId(finalClientId);
                    setHasClientId(true);
                    setClientSecret(finalSecret);
                    setHasSecret(true);
                }

                if (grantType === "password" && username && password) {
                    credentials.push({ credential_type: "USERNAME", value: username });
                    credentials.push({ credential_type: "PASSWORD", value: password });
                }

                // Only call API if we have credentials to save
                if (credentials.length > 0) {
                    await setDataSourceCredentials(
                        dataSource.data_source_id,
                        credentials,
                        projectId,
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
        if (isPublished) setIsEditing(true);
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
        if (isPublished) setIsEditing(false);
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
                {!isEditing && !isPublished ? (
                    <Button onClick={() => setIsEditing(true)} disabled={disabled}>
                        <Shield className="h-4 w-4 mr-2" />
                        Edit
                    </Button>
                ) : isEditing ? (
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
                ) : null}
            </div>

            <Separator />

            <div className="space-y-6">
                <div className="space-y-3">
                    <Label className="text-sm font-medium">Authentication Method</Label>

                    <RadioGroup
                        value={authMethod}
                        onValueChange={(value) =>
                            isEditing && !isPublished && setAuthMethod(value as AuthMethod)
                        }
                        disabled={!isEditing || disabled || isPublished}
                        className="space-y-2"
                    >
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem
                                value="none"
                                id="auth-none"
                                disabled={!isEditing || disabled || isPublished}
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
                                disabled={!isEditing || disabled || isPublished}
                            />
                            <Label
                                htmlFor="auth-basic"
                                className="text-sm font-normal cursor-pointer"
                            >
                                Basic Authentication
                            </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem
                                value="bearer"
                                id="auth-bearer"
                                disabled={!isEditing || disabled || isPublished}
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
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-medium">Credentials</h4>
                                {((isEditing && !isPublished) || isPublished) &&
                                    !isEditingCredentials &&
                                    (hasClientId || hasSecret) && (
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={handleEditCredentials}
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
                                    value={isEditingCredentials ? clientIdInput : clientId || ""}
                                    onChange={(e) => {
                                        setClientIdInput(e.target.value);
                                        if (credentialsError) setCredentialsError("");
                                    }}
                                    disabled={!isEditingCredentials}
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
                                    value={
                                        isEditingCredentials
                                            ? clientSecretInput
                                            : hasSecret
                                              ? "••••••••"
                                              : ""
                                    }
                                    onChange={(e) => {
                                        setClientSecretInput(e.target.value);
                                        if (credentialsError) setCredentialsError("");
                                    }}
                                    disabled={!isEditingCredentials}
                                    placeholder={
                                        isEditingCredentials ? "Enter new client secret" : ""
                                    }
                                />
                                <p className="text-xs text-muted-foreground">
                                    Secret is encrypted and never exposed in API responses.
                                </p>
                            </div>
                        </div>
                    </>
                )}

                {authMethod === "bearer" && !(isPublished && isEditingCredentials) && (
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
                                    disabled={!isEditing || disabled || isPublished}
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
                                    disabled={!isEditing || disabled || isPublished}
                                >
                                    <SelectTrigger id="grant-type">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="client_credentials">
                                            Client Credentials
                                        </SelectItem>
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
                                    disabled={!isEditing || disabled || isPublished}
                                    placeholder="read write"
                                />
                            </div>

                            {grantType === "password" && !(isPublished && isEditingCredentials) && (
                                <>
                                    <Separator className="my-4" />
                                    <h5 className="text-sm font-medium">
                                        Password Grant Credentials
                                    </h5>

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
                                            disabled={!isEditing || disabled || isPublished}
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
                                            disabled={!isEditing || disabled || isPublished}
                                            placeholder={
                                                hasPassword ? "••••••••" : "Enter password"
                                            }
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

                {isPublished && !isEditingCredentials && (
                    <p className="text-xs text-muted-foreground mt-4">
                        Only credentials can be updated for published data sources. Authentication
                        configuration (method, token URL, grant type, scope) is read-only.
                    </p>
                )}
            </div>

            <ConfirmCredentialUpdateDialog
                open={showConfirmDialog}
                onConfirm={performSave}
                onCancel={() => setShowConfirmDialog(false)}
                isLoading={isSaving}
            />
        </div>
    );
}
