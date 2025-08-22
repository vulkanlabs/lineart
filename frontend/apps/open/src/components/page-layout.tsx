import { PageLayout as SharedPageLayout, type PageLayoutConfig } from "@vulkanlabs/base";
import "@/app/globals.css";

// Global scope page layout configuration
const globalScopeLayoutConfig: PageLayoutConfig = {
    useCustomScrollClasses: true,
    useResponsiveBreakpoints: true,
};

// Global scope PageLayout wrapper
export function PageLayout(props: Parameters<typeof SharedPageLayout>[0]) {
    return <SharedPageLayout {...props} config={globalScopeLayoutConfig} />;
}
