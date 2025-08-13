import { PageLayout as SharedPageLayout, type PageLayoutConfig } from "@vulkanlabs/base";
import "@/app/globals.css";

// Re-export shared types
export * from "@vulkanlabs/base";

// Local page layout configuration
const layoutConfig: PageLayoutConfig = {
    useCustomScrollClasses: true,
    useResponsiveBreakpoints: true,
};

// Local PageLayout wrapper
export function PageLayout(props: Parameters<typeof SharedPageLayout>[0]) {
    return <SharedPageLayout {...props} config={layoutConfig} />;
}
