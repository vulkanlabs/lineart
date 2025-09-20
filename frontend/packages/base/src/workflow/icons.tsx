import {
    Link,
    ArrowRightFromLine,
    Split,
    ArrowDown01,
    Code2,
    Network,
    FormInput,
    Puzzle,
    GitBranch,
} from "lucide-react";

/**
 * Mapping of node types to their corresponding Lucide React icons
 * This mapping is used throughout the workflow components to display consistent icons
 */
export const iconMapping = {
    CONNECTION: Link,
    TRANSFORM: Code2,
    BRANCH: GitBranch,
    DECISION: Split,
    INPUT: FormInput,
    DATA_INPUT: ArrowDown01,
    TERMINATE: ArrowRightFromLine,
    POLICY: Network,
    COMPONENT: Puzzle,
} as const;

/**
 * Type for icon keys (node types that have icons)
 */
export type IconType = keyof typeof iconMapping;
