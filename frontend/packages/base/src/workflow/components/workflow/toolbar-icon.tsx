import React from "react";
import { LucideIcon } from "lucide-react";

/**
 * Props for the ToolbarIcon component
 */
export interface ToolbarIconProps {
    /** The Lucide icon component to render */
    icon: LucideIcon;
    /** Optional custom size (defaults to 16) */
    size?: number;
    /** Optional custom stroke width (defaults to 1.5) */
    strokeWidth?: number;
    /** Optional custom stroke color (defaults to #374151) */
    strokeColor?: string;
}

/**
 * Reusable toolbar icon component with consistent styling
 * Eliminates duplication of common icon properties across toolbar buttons
 */
export function ToolbarIcon({
    icon: Icon,
    size = 16,
    strokeWidth = 1.5,
    strokeColor = "#374151",
}: ToolbarIconProps) {
    return (
        <Icon
            size={size}
            strokeWidth={strokeWidth}
            style={{
                stroke: strokeColor,
                fill: "none",
                display: "block",
                color: strokeColor,
            }}
        />
    );
}
