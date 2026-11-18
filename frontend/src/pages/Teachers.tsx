import { useState, useEffect } from "react";
import { Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { teachersApi } from "@/services/api";
import { AddTeacherDialog } from "@/components/teachers/AddTeacherDialog";

export default function Teachers() {
    const [teachers, setTeachers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchTeachers = async () => {
        setLoading(true);
        try {
            const response = await teachersApi.getAll();
            setTeachers(response.data);
        } catch (error) {
            console.error("Failed to fetch teachers", error);
            // Fallback or empty
            setTeachers([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeachers();
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure?")) return;
        try {
            await teachersApi.delete(id);
            fetchTeachers();
        } catch {
            alert("Failed to delete");
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Teachers</h2>
                    <p className="text-muted-foreground">Manage faculty members and their constraints.</p>
                </div>
                <AddTeacherDialog onTeacherAdded={fetchTeachers} />
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Faculty List</CardTitle>
                    <CardDescription>
                        A list of all teachers in the department.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Weekly Hours</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-8">
                                            <div className="flex justify-center"><Loader2 className="animate-spin" /></div>
                                        </TableCell>
                                    </TableRow>
                                ) : teachers.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center">No teachers found.</TableCell>
                                    </TableRow>
                                ) : (
                                    teachers.map((teacher) => (
                                        <TableRow key={teacher.id}>
                                            <TableCell className="font-medium">{teacher.name}</TableCell>
                                            <TableCell>{teacher.email}</TableCell>
                                            <TableCell>{teacher.weekly_hours || 0} hrs</TableCell>
                                            <TableCell className="text-right">
                                                <Button variant="ghost" size="icon">
                                                    <Pencil className="h-4 w-4" />
                                                </Button>
                                                <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDelete(teacher.id)}>
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
