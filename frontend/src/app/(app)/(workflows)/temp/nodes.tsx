import { memo } from "react";

import { NodeProps, Handle, Position } from "@xyflow/react";

import { BaseNode } from "@/components/flow/base-node";
import {
    NodeHeader,
    NodeHeaderTitle,
    NodeHeaderActions,
    NodeHeaderMenuAction,
    NodeHeaderIcon,
    NodeHeaderDeleteAction,
} from "@/components/flow/node-header";
import {
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Rocket } from "lucide-react";

export const NodeHeaderDemo = memo(({ selected }: NodeProps) => {
    return (
        <BaseNode selected={selected} className="px-3 py-2">
            <NodeHeader className="-mx-3 -mt-2 border-b">
                <NodeHeaderIcon>
                    <Rocket />
                </NodeHeaderIcon>
                <NodeHeaderTitle>Node Title</NodeHeaderTitle>
                <NodeHeaderActions>
                    <NodeHeaderMenuAction label="Expand account options">
                        <DropdownMenuLabel>My Account</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>Profile</DropdownMenuItem>
                        <DropdownMenuItem>Billing</DropdownMenuItem>
                        <DropdownMenuItem>Team</DropdownMenuItem>
                        <DropdownMenuItem>Subscription</DropdownMenuItem>
                    </NodeHeaderMenuAction>
                    <NodeHeaderDeleteAction />
                </NodeHeaderActions>
            </NodeHeader>
            <div className="mt-2">Node Content</div>
            <Handle type="target" position={Position.Top} />
            <Handle type="source" position={Position.Bottom} />
        </BaseNode>
    );
});
