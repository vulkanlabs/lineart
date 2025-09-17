"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from "react";
import { setGlobalToastRef } from "./toast-helpers";

export interface Toast {
    id: string;
    title: string;
    description?: string;
    variant?: "default" | "destructive" | "success";
    duration?: number;
    dismissible?: boolean;
}

interface ToastContextType {
    toasts: Toast[];
    addToast: (toast: Omit<Toast, "id">) => void;
    removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) throw new Error("useToast must be used within a ToastProvider");
    return context;
}

interface ToastProviderProps {
    children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((toast: Omit<Toast, "id">) => {
        const id = Math.random().toString(36).substring(2, 9);
        const newToast: Toast = {
            id,
            duration: 5000,
            dismissible: true,
            variant: "default",
            ...toast,
        };

        setToasts((prev) => [...prev, newToast]);

        // Auto-dismiss after duration
        if (newToast.duration && newToast.duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, newToast.duration);
        }
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    // Set up global toast reference for use outside React components
    useEffect(() => {
        const globalToast = (title: string, options?: any) => {
            addToast({
                title,
                description: options?.description,
                duration: options?.duration,
                dismissible: options?.dismissible,
                variant: options?.variant || "default",
            });
        };

        setGlobalToastRef(globalToast);

        return () => {
            setGlobalToastRef(() => {});
        };
    }, [addToast]);

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
        </ToastContext.Provider>
    );
}