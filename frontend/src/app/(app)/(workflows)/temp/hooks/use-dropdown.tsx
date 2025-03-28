import { set } from "date-fns";
import { useEffect, useRef, useState } from "react";

export function useDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [connectingNode, setConnectingNode] = useState(null);
    const ref = useRef<HTMLDivElement>(null);

    const toggleDropdown = (connectingNode) => {
        setIsOpen((prev) => !prev)
        setConnectingNode(connectingNode);
    };

    const closeDropdown = () => {
        setIsOpen(false);
        setConnectingNode(null);
    }

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

    return { isOpen, connectingNode, toggleDropdown, closeDropdown, ref };
}
