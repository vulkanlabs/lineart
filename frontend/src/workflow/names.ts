export function standardizeNodeName(name: string): string {
    return name.replace(/\s+/g, "_").toLowerCase();
}
