import { InnerNavbar, InnerNavbarSectionProps } from "@/components/inner-navbar";
import { fetchComponent } from "@/lib/api";

export default async function Layout(props) {
    const params = await props.params;

    const { children } = props;

    const component = await fetchComponent(params.component_id);
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Component:", value: component.name },
    ];

    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar sections={innerNavbarSections} />
            {children}
        </div>
    );
}
