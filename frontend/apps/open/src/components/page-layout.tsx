import { PageLayout as SharedPageLayout, type PageLayoutConfig } from "@vulkanlabs/base";
import "@/app/globals.css";

// Re-export shared types
export * from "@vulkanlabs/base";

// OSS-specific configuration
const ossConfig: PageLayoutConfig = {
    useCustomScrollClasses: true,
    useResponsiveBreakpoints: true,
};

// OSS-specific PageLayout wrapper
export function PageLayout(props: Parameters<typeof SharedPageLayout>[0]) {
    return <SharedPageLayout {...props} config={ossConfig} />;
}
