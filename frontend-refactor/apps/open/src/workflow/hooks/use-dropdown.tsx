import { useEffect, useRef, useState } from "react";

export function useDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [connectingHandle, setConnectingHandle] = useState(null);
    const ref = useRef<HTMLDivElement>(null);

    const toggleDropdown = (connectingHandle) => {
        setIsOpen((prev) => !prev);
        setConnectingHandle(connectingHandle);
    };

    const closeDropdown = () => {
        setIsOpen(false);
        setConnectingHandle(null);
    };

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

    return { isOpen, connectingHandle, toggleDropdown, closeDropdown, ref };
}
