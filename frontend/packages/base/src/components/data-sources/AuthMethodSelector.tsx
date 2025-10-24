"use client";

import { Label, RadioGroup, RadioGroupItem } from "../ui";

export type AuthMethod = "none" | "basic" | "bearer";

interface AuthMethodSelectorProps {
    value: AuthMethod;
    onChange: (method: AuthMethod) => void;
    disabled?: boolean;
}

export function AuthMethodSelector({ value, onChange, disabled = false }: AuthMethodSelectorProps) {
    return (
        <div className="space-y-3">
            <Label className="text-sm font-medium">Authentication Method</Label>
            <RadioGroup
                value={value}
                onValueChange={(val) => onChange(val as AuthMethod)}
                disabled={disabled}
                className="space-y-3"
            >
                <div className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors">
                    <RadioGroupItem value="none" id="auth-none" disabled={disabled} />
                    <div className="flex-1">
                        <Label
                            htmlFor="auth-none"
                            className="text-sm font-medium cursor-pointer"
                        >
                            No Authentication
                        </Label>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            Public API without authentication
                        </p>
                    </div>
                </div>

                <div className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors">
                    <RadioGroupItem value="basic" id="auth-basic" disabled={disabled} />
                    <div className="flex-1">
                        <Label
                            htmlFor="auth-basic"
                            className="text-sm font-medium cursor-pointer"
                        >
                            Basic Authentication
                        </Label>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            Username and password encoded in Base64
                        </p>
                    </div>
                </div>

                <div className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors">
                    <RadioGroupItem value="bearer" id="auth-bearer" disabled={disabled} />
                    <div className="flex-1">
                        <Label
                            htmlFor="auth-bearer"
                            className="text-sm font-medium cursor-pointer"
                        >
                            Bearer / OAuth 
                        </Label>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            Token-based authentication with automatic refresh
                        </p>
                    </div>
                </div>
            </RadioGroup>
        </div>
    );
}
