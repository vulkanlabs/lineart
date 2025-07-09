import { useEffect, useRef, useState } from "react";

/**
 * Type for connecting handle information
 */
export type ConnectingHandle = {
    nodeId: string;
    id: string | null;
} | null;

/**
 * Hook for managing dropdown state in workflow context
 * Used for node creation dropdown that appears when dragging connections
 */
export function useDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [connectingHandle, setConnectingHandle] = useState<ConnectingHandle>(null);
    const ref = useRef<HTMLDivElement>(null);

    /**
     * Toggle the dropdown open/closed state
     */
    const toggleDropdown = (handle: ConnectingHandle) => {
        setIsOpen((prev) => !prev);
        setConnectingHandle(handle);
    };

    /**
     * Close the dropdown and reset state
     */
    const closeDropdown = () => {
        setIsOpen(false);
        setConnectingHandle(null);
    };

    /**
     * Handle clicking outside the dropdown to close it
     */
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (ref.current && !ref.current.contains(event.target as Node)) {
                closeDropdown();
            }
        };

        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isOpen]);

    return {
        isOpen,
        connectingHandle,
        toggleDropdown,
        closeDropdown,
        ref,
    };
}
