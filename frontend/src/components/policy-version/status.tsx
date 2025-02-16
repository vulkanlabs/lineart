export function VersionStatus({ value }) {
    const getColor = (status: string) => {
        switch (status) {
            case "active":
                return "bg-green-200";
            case "inactive":
                return "bg-gray-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}
