import {
    PageLayout as SharedPageLayout,
    type PageLayoutConfig,
    type SidebarTitleProps,
    type SidebarSectionProps,
    type SidebarProps,
    type PageContentProps,
} from "@vulkanlabs/base";
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

export type {
    SidebarTitleProps,
    SidebarSectionProps,
    SidebarProps,
    PageContentProps,
    PageLayoutConfig,
};
