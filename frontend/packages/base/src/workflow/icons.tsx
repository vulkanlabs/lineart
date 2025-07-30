import { Link, ArrowRightFromLine, Split, ArrowDown01, Code2, Network, FormInput } from "lucide-react";

/**
 * Mapping of node types to their corresponding Lucide React icons
 * This mapping is used throughout the workflow components to display consistent icons
 */
export const iconMapping = {
    CONNECTION: Link,
    TRANSFORM: Code2,
    BRANCH: Split,
    INPUT: FormInput,
    DATA_INPUT: ArrowDown01,
    TERMINATE: ArrowRightFromLine,
    POLICY: Network,
} as const;

/**
 * Type for icon keys (node types that have icons)
 */
export type IconType = keyof typeof iconMapping;
