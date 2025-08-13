import { PageLayout as SharedPageLayout, type PageLayoutConfig } from "@vulkanlabs/base";
import "@/app/globals.css";

// Re-export shared types
export * from "@vulkanlabs/base";

// Global scope page layout configuration
const globalScopeLayoutConfig: PageLayoutConfig = {
    useCustomScrollClasses: true,
    useResponsiveBreakpoints: true,
};

// Global scope PageLayout wrapper
export function PageLayout(props: Parameters<typeof SharedPageLayout>[0]) {
    return <SharedPageLayout {...props} config={globalScopeLayoutConfig} />;
}
