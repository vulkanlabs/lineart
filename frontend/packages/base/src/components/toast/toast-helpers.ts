import { useToast as useToastContext } from "./toast-context";

/**
 * Hook that provides toast functions compatible with Sonner
 */
export function useToastHelpers() {
    const { addToast } = useToastContext();

    // Main toast function compatible with Sonner
    const toast = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
        },
    ) => {
        addToast({
            title,
            description: options?.description,
            duration: options?.duration,
            dismissible: options?.dismissible,
            variant: "default",
        });
    };

    // Success variant
    toast.success = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
        },
    ) => {
        addToast({
            title,
            description: options?.description,
            duration: options?.duration || 2000,
            dismissible: options?.dismissible,
            variant: "success",
        });
    };

    // Error variant
    toast.error = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
        },
    ) => {
        addToast({
            title,
            description: options?.description,
            duration: options?.duration || 5000,
            dismissible: options?.dismissible,
            variant: "destructive",
        });
    };

    return { toast };
}

/**
 * Standalone toast functions for use outside of React components
 * This allows creating a global toast function similar to Sonner
 */
let globalToastRef: ((title: string, options?: any) => void) | null = null;

export function setGlobalToastRef(toastFn: (title: string, options?: any) => void) {
    globalToastRef = toastFn;
}

export function createGlobalToast() {
    const toast = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
            variant?: "default" | "destructive" | "success";
        },
    ) => {
        if (globalToastRef) globalToastRef(title, options);
    };

    // Success variant
    toast.success = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
        },
    ) => {
        toast(title, {
            ...options,
            variant: "success",
            duration: options?.duration || 2000,
        });
    };

    // Error variant
    toast.error = (
        title: string,
        options?: {
            description?: string;
            duration?: number;
            dismissible?: boolean;
        },
    ) => {
        toast(title, {
            ...options,
            variant: "destructive",
            duration: options?.duration || 5000,
        });
    };

    return toast;
}
