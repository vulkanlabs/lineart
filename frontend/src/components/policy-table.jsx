import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { useRouter } from 'next/navigation';


export function PolicyTable({ policies }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>A lista das suas políticas criadas.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead>Versão Ativa</TableHead>
                    <TableHead>Última Atualização</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {policies.map((policy) => (
                    <TableRow key={policy.policy_id} className="cursor-pointer" onClick={() => router.push(`/policies/${policy.policy_id}`)} >
                        <TableCell>{policy.policy_id}</TableCell>
                        <TableCell>{policy.name}</TableCell>
                        <TableCell>{policy.description.length > 0 ? policy.description : "-"}</TableCell>
                        <TableCell>{policy.active_policy_version_id !== null ? policy.active_policy_version_id : "-"}</TableCell>
                        <TableCell>{policy.last_updated_at}</TableCell>
                    </TableRow>

                ))}
            </TableBody>
        </Table >
    );
}
