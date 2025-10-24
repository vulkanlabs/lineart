"use client";

import { Info, RefreshCw } from "lucide-react";
import { Input, Label } from "../ui";

export type GrantType = "client_credentials" | "password" | "authorization_code" | "implicit" | "refresh_token";

interface BearerAuthConfigProps {
    tokenUrl: string;
    grantType: GrantType;
    scope?: string;
    clientId: string;
    clientSecret: string;
    onTokenUrlChange: (value: string) => void;
    onGrantTypeChange: (value: GrantType) => void;
    onScopeChange: (value: string) => void;
    onClientIdChange: (value: string) => void;
    onClientSecretChange: (value: string) => void;
    disabled?: boolean;
}

export function BearerAuthConfig({
    tokenUrl,
    grantType,
    scope = "",
    clientId,
    clientSecret,
    onTokenUrlChange,
    onGrantTypeChange,
    onScopeChange,
    onClientIdChange,
    onClientSecretChange,
    disabled = false,
}: BearerAuthConfigProps) {
    return (
        <div className="space-y-4 rounded-lg border p-4 bg-muted/30">
            <div>
                <h4 className="text-sm font-semibold mb-3">Bearer / OAuth Configuration</h4>
                <p className="text-xs text-muted-foreground mb-4">
                    Token-based authentication with automatic caching and refresh
                </p>
            </div>

            <div className="space-y-4">
                <div>
                    <Label htmlFor="bearer-token-url" className="text-sm font-medium">
                        Token URL <span className="text-destructive">*</span>
                    </Label>
                    <Input
                        id="bearer-token-url"
                        type="url"
                        value={tokenUrl}
                        onChange={(e) => onTokenUrlChange(e.target.value)}
                        disabled={disabled}
                        placeholder="https://auth.example.com/oauth/token"
                        className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        OAuth token endpoint for authentication
                    </p>
                </div>

                <div>
                    <Label htmlFor="bearer-grant-type" className="text-sm font-medium">
                        Grant Type <span className="text-destructive">*</span>
                    </Label>
                    <select
                        id="bearer-grant-type"
                        value={grantType}
                        onChange={(e) => onGrantTypeChange(e.target.value as GrantType)}
                        disabled={disabled}
                        className={`mt-1.5 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                    >
                        <option value="client_credentials">Client Credentials</option>
                        <option value="password">Password</option>
                        <option value="authorization_code">Authorization Code</option>
                        <option value="implicit">Implicit</option>
                        <option value="refresh_token">Refresh Token</option>
                    </select>
                    <p className="text-xs text-muted-foreground mt-1">
                        OAuth grant type flow
                    </p>
                </div>

                <div>
                    <Label htmlFor="bearer-scope" className="text-sm font-medium">
                        Scope <span className="text-muted-foreground text-xs">(Optional)</span>
                    </Label>
                    <Input
                        id="bearer-scope"
                        type="text"
                        value={scope}
                        onChange={(e) => onScopeChange(e.target.value)}
                        disabled={disabled}
                        placeholder="api.read api.write"
                        className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        Space-separated list of scopes
                    </p>
                </div>

                <div className="pt-2 border-t">
                    <h5 className="text-sm font-medium mb-3">Client Credentials</h5>

                    <div className="space-y-4">
                        <div>
                            <Label htmlFor="bearer-client-id" className="text-sm font-medium">
                                Client ID <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="bearer-client-id"
                                type="text"
                                value={clientId}
                                onChange={(e) => onClientIdChange(e.target.value)}
                                disabled={disabled}
                                placeholder="my-client-id-123"
                                className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                            />
                        </div>

                        <div>
                            <Label htmlFor="bearer-client-secret" className="text-sm font-medium">
                                Client Secret <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="bearer-client-secret"
                                type="password"
                                value={clientSecret}
                                onChange={(e) => onClientSecretChange(e.target.value)}
                                disabled={disabled}
                                placeholder={disabled ? "********" : "Enter client secret"}
                                className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
