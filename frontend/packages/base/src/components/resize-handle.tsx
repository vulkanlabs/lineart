"use client";

import React from "react";
import { PanelResizeHandle } from "react-resizable-panels";

interface ResizeHandleProps {
    direction: "horizontal" | "vertical";
    onDoubleClick?: () => void;
}

export function ResizeHandle({ direction, onDoubleClick }: ResizeHandleProps) {
    const isHorizontal = direction === "horizontal";
    
    return (
        <PanelResizeHandle 
            className={`
                ${isHorizontal ? "w-1.5 cursor-col-resize" : "h-1.5 cursor-row-resize"}
                bg-gray-200 hover:bg-gray-300 active:bg-blue-400
                transition-all duration-200 
                relative group
            `}
            onDoubleClick={onDoubleClick}
            title="Drag to resize • Double-click to reset"
        >
            <GripIndicator direction={direction} />
        </PanelResizeHandle>
    );
}

function GripIndicator({ direction }: { direction: "horizontal" | "vertical" }) {
    const isHorizontal = direction === "horizontal";
    
    return (
        <div 
            className={`
                absolute ${isHorizontal ? "inset-y-0 left-1/2 -translate-x-1/2" : "inset-x-0 top-1/2 -translate-y-1/2"}
                flex ${isHorizontal ? "flex-col" : "flex-row"} 
                items-center justify-center gap-0.5
                opacity-40 group-hover:opacity-60 transition-opacity pointer-events-none
            `}
        >
            {[1, 2, 3].map((dot) => (
                <div 
                    key={dot}
                    className={`${isHorizontal ? "w-0.5 h-3" : "h-0.5 w-3"} bg-gray-600 rounded-full`} 
                />
            ))}
        </div>
    );
}