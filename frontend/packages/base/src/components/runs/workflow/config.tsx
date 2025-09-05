import { LayoutOptions } from "elkjs/lib/elk-api";
import {
    Link,
    ArrowRightFromLine,
    Split,
    ArrowDown01,
    Code2,
    Network,
    FormInput,
    Puzzle,
    CheckCircle2,
    XCircle,
    SkipForward,
} from "lucide-react";
import { NodeStatus } from "./utils";

export const nodeConfig: {
    [key: string]: {
        type: string;
        icon: React.ComponentType<any>;
    };
} = {
    CONNECTION: { type: "common", icon: Link },
    COMPONENT: { type: "common", icon: Puzzle },
    BRANCH: { type: "common", icon: Split },
    DATA_INPUT: { type: "common", icon: ArrowDown01 },
    DECISION: { type: "common", icon: Split },
    INPUT: { type: "entry", icon: FormInput },
    POLICY: { type: "common", icon: Network },
    TERMINATE: { type: "terminate", icon: ArrowRightFromLine },
    TRANSFORM: { type: "common", icon: Code2 },
};

export const nodeStatusConfig: {
    [key in NodeStatus]: {
        icon: React.ComponentType<any>;
        iconClassName: string;
        styles: string;
    };
} = {
    [NodeStatus.SUCCESS]: {
        icon: CheckCircle2,
        iconClassName: "text-green-600",
        styles: "bg-green-50 border-green-300 hover:border-green-400 hover:shadow-green-100",
    },
    [NodeStatus.ERROR]: {
        icon: XCircle,
        iconClassName: "text-red-600",
        styles: "bg-red-50 border-red-300 hover:border-red-400 hover:shadow-red-100",
    },
    [NodeStatus.SKIPPED]: {
        icon: SkipForward,
        iconClassName: "text-gray-400",
        styles: "bg-gray-50 border-gray-300 hover:border-gray-400 hover:shadow-gray-100",
    },
};

export const defaultElkOptions: LayoutOptions = {
    "elk.algorithm": "layered",
    "elk.layered.nodePlacement.strategy": "SIMPLE",
    "elk.layered.nodePlacement.bk.fixedAlignment": "BALANCED",
    "elk.layered.spacing.nodeNodeBetweenLayers": "50",
    "elk.spacing.nodeNode": "80",
    "elk.aspectRatio": "1.0",
    "elk.center": "true",
    "elk.direction": "RIGHT",
};
