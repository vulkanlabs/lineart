"use client";

import React, { useEffect, useState } from "react";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { cn } from "../../lib/utils";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import type { Toast } from "./toast-context";

interface ToastProps {
    toast: Toast;
    onRemove: (id: string) => void;
}

const variantStyles = {
    default: "border-border bg-background text-foreground",
    destructive: "border-destructive/50 bg-destructive text-destructive-foreground",
    success: "border-green-500/50 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-50",
};

const iconMap = {
    default: Info,
    destructive: AlertCircle,
    success: CheckCircle,
};

export function ToastComponent({ toast, onRemove }: ToastProps) {
    const [isVisible, setIsVisible] = useState(false);
    const [isExiting, setIsExiting] = useState(false);

    const Icon = iconMap[toast.variant || "default"];

    useEffect(() => {
        const timer = setTimeout(() => setIsVisible(true), 10);
        return () => clearTimeout(timer);
    }, []);

    const handleRemove = () => {
        if (isExiting) return;

        setIsExiting(true);
        setIsVisible(false);

        setTimeout(() => {
            onRemove(toast.id);
        }, 200);
    };

    return (
        <Card
            className={cn(
                "w-full max-w-sm shadow-lg transition-all duration-200 ease-in-out transform",
                variantStyles[toast.variant || "default"],
                isVisible && !isExiting
                    ? "translate-x-0 opacity-100 scale-100"
                    : "translate-x-full opacity-0 scale-95",
            )}
        >
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium leading-none">{toast.title}</p>
                        {toast.description && (
                            <p className="text-sm opacity-90">{toast.description}</p>
                        )}
                    </div>
                    {toast.dismissible && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 shrink-0 opacity-60 hover:opacity-100"
                            onClick={handleRemove}
                        >
                            <X className="h-4 w-4" />
                            <span className="sr-only">Close</span>
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
