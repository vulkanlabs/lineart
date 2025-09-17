"use client";

import React from "react";
import { useToast } from "./toast-context";
import { ToastComponent } from "./toast";

export function ToastContainer() {
    const { toasts, removeToast } = useToast();

    if (toasts.length === 0) return null;

    return (
        <div className="fixed bottom-4 right-4 z-[200] flex flex-col-reverse gap-2 w-full max-w-sm pointer-events-none">
            {toasts.map((toast) => (
                <div key={toast.id} className="pointer-events-auto">
                    <ToastComponent toast={toast} onRemove={removeToast} />
                </div>
            ))}
        </div>
    );
}