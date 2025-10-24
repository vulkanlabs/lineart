"use client";

import { Info } from "lucide-react";
import { Input, Label } from "../ui";

interface BasicAuthConfigProps {
    clientId: string;
    clientSecret: string;
    onClientIdChange: (value: string) => void;
    onClientSecretChange: (value: string) => void;
    disabled?: boolean;
}

export function BasicAuthConfig({
    clientId,
    clientSecret,
    onClientIdChange,
    onClientSecretChange,
    disabled = false,
}: BasicAuthConfigProps) {
    return (
        <div className="space-y-4 rounded-lg border p-4 bg-muted/30">
            <div>
                <h4 className="text-sm font-semibold mb-3">Basic Authentication Configuration</h4>
                <p className="text-xs text-muted-foreground mb-4">
                    Credentials will be Base64 encoded as: <code className="bg-muted px-1 py-0.5 rounded text-xs">Authorization: Basic &lt;encoded&gt;</code>
                </p>
            </div>

            <div className="space-y-4">
                <div>
                    <Label htmlFor="basic-client-id" className="text-sm font-medium">
                        Client ID
                    </Label>
                    <Input
                        id="basic-client-id"
                        type="text"
                        value={clientId}
                        onChange={(e) => onClientIdChange(e.target.value)}
                        disabled={disabled}
                        placeholder="my-client-id-123"
                        className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        Client identifier for Basic authentication
                    </p>
                </div>

                <div>
                    <Label htmlFor="basic-client-secret" className="text-sm font-medium">
                        Client Secret
                    </Label>
                    <Input
                        id="basic-client-secret"
                        type="password"
                        value={clientSecret}
                        onChange={(e) => onClientSecretChange(e.target.value)}
                        disabled={disabled}
                        placeholder={disabled ? "********" : "Enter client secret"}
                        className={`mt-1.5 font-mono text-sm ${!disabled ? "" : "!text-foreground !opacity-100"}`}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        Secret key (encrypted at rest)
                    </p>
                </div>
            </div>

            <div className="flex gap-2 items-start p-3 rounded-lg border border-blue-200 bg-blue-50 dark:bg-blue-950/20">
                <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-blue-900 dark:text-blue-100">
                    <strong>Security:</strong> CLIENT_SECRET is encrypted and never returned in API responses.
                </p>
            </div>
        </div>
    );
}
