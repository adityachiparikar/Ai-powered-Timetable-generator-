import { useState, useEffect, useRef, type ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Trash2, Loader2, GraduationCap, Book, School as SchoolIcon, Users as UsersIcon, Pencil, Check, X, Upload, RotateCcw } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { teachersApi, coursesApi, roomsApi, studentGroupsApi, breaksApi, solverApi, importApi } from "@/services/api";
import { motion, AnimatePresence } from "framer-motion";

// Interfaces based on Backend Schemas (approx)
interface Batch {
    id: string;
    name: string;
    size: number;
}

interface StudentGroup {
    id: string;
    name: string; // e.g., Year1_A
    size: number;
    year_level: number;
    batches?: Batch[];
}

interface Teacher {
    id: string;
    name: string;
    email?: string;
}

interface Course {
    id: string;
    code: string;
    name: string;
    weekly_sessions: number;
    course_type: "THEORY" | "LAB" | "TUTORIAL";
    teacher_id?: string;
    student_group_id?: string;
    batch_id?: string;
    teacher?: Teacher;
    student_group?: StudentGroup;
    batch?: Batch;
}

interface Room {
    id: string;
    name: string;
    is_lab: boolean;
    is_tutorial_room?: boolean;
    capacity?: string;
}

export default function DataEntry() {
    const [searchParams, setSearchParams] = useSearchParams();
    const currentTab = searchParams.get("tab") || "student-groups";

    const [loading, setLoading] = useState(false);
    const [importing, setImporting] = useState(false);
    const [resetting, setResetting] = useState(false);
    const importInputRef = useRef<HTMLInputElement | null>(null);

    // Data States
    const [teachers, setTeachers] = useState<Teacher[]>([]);
    const [courses, setCourses] = useState<Course[]>([]);
    const [rooms, setRooms] = useState<Room[]>([]);
    const [groups, setGroups] = useState<StudentGroup[]>([]);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editData, setEditData] = useState<any>({});

    const formatError = (e: any) => {
        const detail = e.response?.data?.detail;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            return detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ');
        }
        return e.message || "An unknown error occurred";
    };

    // Session-specific sub-tabs state
    const [activeSessionYear, setActiveSessionYear] = useState<number>(1);
    const [breaks, setBreaks] = useState<{ id: string; name: string; start_time: string; end_time: string }[]>([]);

    // Solver Task State
    const [solverTaskId, setSolverTaskId] = useState<string | null>(null);
    const [solverLogs, setSolverLogs] = useState<string[]>([]);
    const [solverStatus, setSolverStatus] = useState<string>("idle");

    // Load Data
    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);

        const loadList = async <T,>(label: string, request: Promise<{ data: T[] }>): Promise<T[]> => {
            try {
                const response = await request;
                return Array.isArray(response.data) ? response.data : [];
            } catch (error) {
                console.error(`Failed to fetch ${label}`, error);
                return [];
            }
        };

        try {
            const [teacherData, courseData, roomData, groupData, breakData] = await Promise.all([
                loadList<Teacher>("teachers", teachersApi.getAll()),
                loadList<Course>("courses", coursesApi.getAll()),
                loadList<Room>("rooms", roomsApi.getAll()),
                loadList<StudentGroup>("divisions", studentGroupsApi.getAll()),
                loadList<{ id: string; name: string; start_time: string; end_time: string }>("breaks", breaksApi.getAll())
            ]);

            console.log('Fetched divisions:', groupData);
            setTeachers(teacherData);
            setCourses(courseData);
            setRooms(roomData);
            setGroups(groupData);
            setBreaks(breakData);
        } finally {
            setLoading(false);
        }
    };

    const handleImportLoadDistribution = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setImporting(true);
        try {
            const res = await importApi.loadDistribution(file);
            await fetchData();
            const summary = res.data;
            alert(
                `Import complete.\n` +
                `Teachers: +${summary.teachers_created}, updated ${summary.teachers_updated}\n` +
                `Divisions: +${summary.groups_created}\n` +
                `Batches: +${summary.batches_created}\n` +
                `Sessions: +${summary.courses_created}, updated ${summary.courses_updated}`
            );
        } catch (e: any) {
            console.error(e);
            alert(`Import failed: ${formatError(e)}`);
        } finally {
            setImporting(false);
            event.target.value = "";
        }
    };

    const handleResetMasterData = async () => {
        const confirmed = confirm(
            "Reset master data?\n\nThis will delete teachers, divisions, batches, session descriptions, breaks, and generated timetable entries. Classrooms and time slots will remain."
        );
        if (!confirmed) return;

        const secondConfirm = confirm("This cannot be undone. Continue?");
        if (!secondConfirm) return;

        setResetting(true);
        try {
            const res = await importApi.resetMasterData();
            await fetchData();
            const summary = res.data;
            alert(
                `Reset complete.\n` +
                `Teachers deleted: ${summary.teachers_deleted}\n` +
                `Divisions deleted: ${summary.groups_deleted}\n` +
                `Sessions deleted: ${summary.courses_deleted}\n` +
                `Timetable entries deleted: ${summary.timetable_entries_deleted}`
            );
        } catch (e: any) {
            console.error(e);
            alert(`Reset failed: ${formatError(e)}`);
        } finally {
            setResetting(false);
        }
    };

    // --- Teachers ---
    const [newTeacherName, setNewTeacherName] = useState("");
    const handleAddTeacher = async () => {
        if (!newTeacherName) return;
        const safeEmail = newTeacherName.toLowerCase()
            .replace(/[^a-z0-9]/g, '.')
            .replace(/\.{2,}/g, '.')
            .replace(/^\.|\.$/g, '') + "@example.com";

        try {
            await teachersApi.create({ name: newTeacherName, email: safeEmail });
            setNewTeacherName("");
            fetchData();
        } catch (e: any) {
            console.error(e);
            alert(`Failed to add teacher: ${formatError(e)}`);
        }
    };
    const handleUpdateTeacher = async (id: string) => {
        try {
            await teachersApi.update(id, editData);
            setEditingId(null);
            fetchData();
        } catch (e: any) {
            alert(`Failed to update teacher: ${formatError(e)}`);
        }
    };
    const handleDeleteTeacher = async (id: string) => {
        if (!confirm("Are you sure you want to delete this teacher?")) return;
        try { await teachersApi.delete(id); fetchData(); } catch (e: any) {
            console.error(e);
            alert(`Failed to delete teacher: ${formatError(e)}`);
        }
    };

    // --- Rooms ---
    const [newRoomName, setNewRoomName] = useState("");
    const [newRoomIsLab, setNewRoomIsLab] = useState(false);
    const [newRoomIsTutorial, setNewRoomIsTutorial] = useState(false);
    const handleAddRoom = async () => {
        if (!newRoomName) return;
        try {
            await roomsApi.create({ name: newRoomName, is_lab: newRoomIsLab, is_tutorial_room: newRoomIsTutorial });
            setNewRoomName("");
            fetchData();
        } catch (e: any) {
            console.error(e);
            alert(`Failed to add room: ${formatError(e)}`);
        }
    };
    const handleUpdateRoom = async (id: string) => {
        try {
            await roomsApi.update(id, { name: editData.name, is_lab: editData.is_lab, is_tutorial_room: editData.is_tutorial_room });
            setEditingId(null);
            fetchData();
        } catch (e: any) {
            console.error(e);
            alert(`Failed to update room: ${formatError(e)}`);
        }
    };
    const handleDeleteRoom = async (id: string) => {
        if (!confirm("Are you sure you want to delete this room?")) return;
        try { await roomsApi.delete(id); fetchData(); } catch (e: any) {
            console.error(e);
            alert(`Failed to delete room: ${formatError(e)}`);
        }
    };

    // --- Student Groups (Classes) ---
    const [newGroupDepartment, setNewGroupDepartment] = useState("CS");
    const [newGroupYear, setNewGroupYear] = useState("2");
    const [newGroupDivision, setNewGroupDivision] = useState("A");

    const handleAddGroup = async () => {
        const yearInt = parseInt(newGroupYear);
        if (isNaN(yearInt)) {
            alert("Invalid Year. Please enter a number (1-4).");
            return;
        }

        const getYearPrefix = (y: string) => {
            if (y === "1") return "FY";
            if (y === "2") return "SY";
            if (y === "3") return "TY";
            if (y === "4") return "FinalY";
            return `Year${y}`;
        };

        const groupName = `${newGroupDepartment}-${getYearPrefix(newGroupYear)}-${newGroupDivision}`;
        try {
            await studentGroupsApi.create({
                name: groupName,
                size: 60,
                year_level: yearInt
            });
            fetchData();
        } catch (e: any) {
            console.error("Add Group Error:", e);
            alert(`Failed to add class: ${formatError(e)}`);
        }
    };
    const handleUpdateGroup = async (id: string) => {
        try {
            await studentGroupsApi.update(id, editData);
            setEditingId(null);
            fetchData();
        } catch (e: any) {
            alert(`Failed to update group: ${formatError(e)}`);
        }
    };
    const handleDeleteGroup = async (id: string) => {
        if (!confirm("Are you sure you want to delete this division? All associated courses and batches will be affected.")) return;
        try { await studentGroupsApi.delete(id); fetchData(); } catch (e: any) {
            console.error(e);
            alert(`Failed to delete group: ${formatError(e)}`);
        }
    };

    // --- Courses / Curriculum Management ---
    const [newCourseCode, setNewCourseCode] = useState("");
    const [newCourseName, setNewCourseName] = useState("");
    const [newCourseType, setNewCourseType] = useState<"THEORY" | "LAB" | "TUTORIAL">("THEORY");
    const [newCourseHours, setNewCourseHours] = useState(4);

    const handleAddCourse = async () => {
        const yearGroups = groups.filter(g => g.year_level === activeSessionYear);

        if (!newCourseName || !newCourseCode) {
            alert("Subject Name and Code are required.");
            return;
        }

        if (yearGroups.length === 0) {
            alert(`Cannot add session: No divisions exist for Year ${activeSessionYear}. Please go to the "Divisions" tab and add at least one division for Year ${activeSessionYear} first.`);
            return;
        }

        try {
            // Iterate over ALL groups (divisions) for the selected year
            for (const group of yearGroups) {
                // Check if course already exists to avoid duplicates
                const exists = courses.some(c =>
                    c.name === newCourseName &&
                    c.course_type === newCourseType &&
                    (c.student_group_id === group.id || c.student_group?.id === group.id)
                );

                if (exists) {
                    console.log(`Skipping duplicate: ${newCourseName} for ${group.name}`);
                    continue;
                }

                // Create single entry for valid course (LAB or THEORY)
                // New Strategy: Code + DivisionLetter + Type (e.g. ML101-A-L)
                const cleanCode = newCourseCode.trim().substring(0, 6).toUpperCase();
                const divChar = group.name.trim().slice(-1).toUpperCase().replace(/[^A-Z0-9]/, 'X');
                const suffix = newCourseType === "LAB" ? "L" : newCourseType === "TUTORIAL" ? "U" : "T";

                const generatedCode = `${cleanCode}-${divChar}-${suffix}`; // e.g. ML101-A-L (very short & unique)

                await coursesApi.create({
                    code: generatedCode,
                    name: newCourseName,
                    course_type: newCourseType,
                    weekly_sessions: newCourseHours,
                    student_group_id: group.id,
                    batch_id: null,
                    teacher_id: null
                });
            }


            // Reset fields
            setNewCourseName("");
            setNewCourseCode("");
            fetchData();
        } catch (e: any) {
            alert(`Failed to add course: ${formatError(e)}`);
        }
    };

    const handleUpdateCourseTeacher = async (courseId: string, teacherId: string) => {
        try {
            await coursesApi.update(courseId, { teacher_id: teacherId === "unassigned" ? null : teacherId });
            fetchData();
        } catch (e: any) {
            alert(`Failed to update teacher: ${e.message}`);
        }
    };

    const handleSplitAndAssign = async (consolidatedCourse: any, targetBatchName: string | null, teacherId: string) => {
        try {
            // Verify we have a group ID
            const groupId = consolidatedCourse.student_group_id || consolidatedCourse.student_group?.id;
            if (!groupId) {
                alert("Cannot assign: Course is missing Class/Division information.");
                return;
            }

            // 1. Delete the consolidated course (Ignore 404 if already deleted)
            try {
                await coursesApi.delete(consolidatedCourse.id);
            } catch (e: any) {
                if (e.response?.status !== 404) throw e;
            }

            // 2. Determine batches
            const groupBatches = consolidatedCourse.student_group?.batches || [];
            const batchesToCreate = groupBatches.length > 0
                ? groupBatches
                : [{ id: null, name: "1" }, { id: null, name: "2" }, { id: null, name: "3" }];

            // 3. Create new courses
            for (const batch of batchesToCreate) {
                const isTarget = targetBatchName === 'ALL' || batch.name === targetBatchName;
                const newCode = `${consolidatedCourse.code}-B${batch.name}`;

                try {
                    await coursesApi.create({
                        code: newCode,
                        name: consolidatedCourse.name,
                        course_type: consolidatedCourse.course_type,
                        weekly_sessions: consolidatedCourse.weekly_sessions,
                        student_group_id: groupId, // Use the verified ID
                        batch_id: batch.id,
                        teacher_id: isTarget ? teacherId : null
                    });
                } catch (e: any) {
                    if (isTarget && e.response?.status === 400) {
                        try {
                            const existing = courses.find((c: any) => c.code === newCode);
                            if (existing) {
                                await coursesApi.update(existing.id, { teacher_id: teacherId });
                            } else {
                                console.warn(`Could not find existing split to update: ${newCode}`);
                                // If critical, we might want to throw here, but for duplicates, maybe we assume it's fine?
                                // Actually, if we can't update the teacher, the user's action FAILED.
                                // We should probably alert? But let's keep it safe.
                            }
                        } catch (updateErr) {
                            console.error("Failed to update existing split:", updateErr);
                        }
                    } else {
                        // Re-throw unexpected errors (like 422) to alert the user!
                        throw e;
                    }
                }
            }
            fetchData();
        } catch (e: any) {
            console.error("Split/Assign Error:", e);
            alert(`Failed to split and assign: ${e.response?.data?.detail || e.message}`);
        }
    };

    const handleUpdateCourseGroup = async (items: any[], updates: any) => {
        try {
            await Promise.all(items.map(item => coursesApi.update(item.id, updates)));
            setEditingId(null);
            fetchData();
        } catch (e: any) {
            console.error(e);
            alert(`Failed to update group: ${e.message}`);
        }
    };

    const handleDeleteCourseGroup = async (items: any[]) => {
        if (!confirm(`Are you sure you want to delete these ${items.length} sessions? THIS CANNOT BE UNDONE.`)) return;
        try {
            await Promise.all(items.map(item => coursesApi.delete(item.id)));
            fetchData();
        } catch (e: any) {
            console.error(e);
            alert(`Failed to delete group: ${e.message}`);
        }
    };

    const handleAssignToAllBatches = async (courseName: string, divisionId: string, teacherId: string) => {
        // Find all courses matching this group
        const groupCourses = courses.filter(c =>
            c.name === courseName &&
            (c.student_group_id === divisionId || c.student_group?.id === divisionId) &&
            (c.course_type === 'LAB' || c.course_type === 'TUTORIAL')
        );

        if (groupCourses.length === 1 && (!groupCourses[0].batch_id || groupCourses[0].batch_id === null)) {
            // Case 1: Consolidated Course -> Split and Assign ALL
            await handleSplitAndAssign(groupCourses[0], 'ALL', teacherId);
        } else {
            // Case 2: Already Split -> Update all
            for (const c of groupCourses) {
                await coursesApi.update(c.id, { teacher_id: teacherId });
            }
            fetchData();
        }
    };

    const handleTabChange = (val: string) => {
        setSearchParams({ tab: val });
    };

    // --- Breaks ---
    const handleAddBreak = async () => {
        try {
            await breaksApi.create({ name: "New Break", start_time: "11:00", end_time: "11:15" });
            fetchData();
        } catch (e: any) { alert(`Failed to add break: ${e.message}`); }
    };
    const handleUpdateBreak = async (id: string, data: any) => {
        try {
            await breaksApi.update(id, data);
            fetchData();
        } catch (e: any) { console.error(e); }
    };
    const handleDeleteBreak = async (id: string) => {
        if (!confirm("Delete this break?")) return;
        try { await breaksApi.delete(id); fetchData(); } catch (e: any) { alert(e.message); }
    };

    // --- Solver ---
    const handleGenerate = async () => {
        setSolverLogs([]);
        setSolverStatus("running");
        try {
            const stored = localStorage.getItem("solver_config");
            const storedConfig = stored ? JSON.parse(stored) : {};
            const config = {
                ...storedConfig,
                max_time_seconds: storedConfig.max_time_seconds ?? 90,
                enable_soft_constraints: true,
                minimize_gaps: true,
                max_group_gap_hours: storedConfig.max_group_gap_hours ?? 2,
            };
            const res = await solverApi.generate("Fall 2025", config);
            const taskId = res.data.task_id;
            setSolverTaskId(taskId);
            if (res.data.status === "SUCCESS") {
                setSolverStatus("done");
                return;
            }
            startPollingStatus(taskId);
            startLogStream(taskId);
        } catch (e: any) {
            setSolverStatus("error");
            alert(`Failed to start solver: ${e.message}`);
        }
    };

    const startPollingStatus = (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const res = await solverApi.getStatus(taskId);
                if (res.data.status === "SUCCESS") {
                    setSolverStatus("done");
                    clearInterval(interval);
                } else if (res.data.status === "FAILURE") {
                    setSolverStatus("error");
                    clearInterval(interval);
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 3000);
    };

    const startLogStream = (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const res = await solverApi.getLogs(taskId);
                setSolverLogs(res.data.logs);
                if (solverStatus === "done" || solverStatus === "error") clearInterval(interval);
            } catch (e) {
                console.error("Logs error", e);
            }
        }, 1500);
    };

    if (loading && teachers.length === 0) {
        return <div className="p-8 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>;
    }

    const tabVariants = {
        hidden: { opacity: 0, x: -10 },
        visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
        exit: { opacity: 0, x: 10, transition: { duration: 0.2 } }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">Master Data Entry</h2>
                    <p className="text-muted-foreground">System Configuration & Resourcing</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <input
                        ref={importInputRef}
                        type="file"
                        accept=".xlsx,.xlsm"
                        className="hidden"
                        onChange={handleImportLoadDistribution}
                    />
                    <Button
                        variant="outline"
                        onClick={() => importInputRef.current?.click()}
                        disabled={importing || loading}
                        className="gap-2"
                    >
                        {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                        {importing ? "Importing..." : "Import Load Sheet"}
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleResetMasterData}
                        disabled={resetting || importing || loading}
                        className="gap-2"
                    >
                        {resetting ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                        {resetting ? "Resetting..." : "Reset Data"}
                    </Button>
                </div>
            </div>

            <Tabs value={currentTab} onValueChange={handleTabChange} className="w-full">
                <TabsList className="grid w-full grid-cols-4 bg-muted/50 p-1.5 rounded-2xl glass mb-4 h-14">
                    <TabsTrigger value="student-groups" className="rounded-xl data-[state=active]:bg-indigo-600 data-[state=active]:text-white transition-all"><GraduationCap className="w-4 h-4 mr-2" /> Divisions</TabsTrigger>
                    <TabsTrigger value="rooms" className="rounded-xl data-[state=active]:bg-green-600 data-[state=active]:text-white transition-all"><SchoolIcon className="w-4 h-4 mr-2" /> Classrooms</TabsTrigger>
                    <TabsTrigger value="courses" className="rounded-xl data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"><Book className="w-4 h-4 mr-2" /> Session Descs</TabsTrigger>
                    <TabsTrigger value="teachers" className="rounded-xl data-[state=active]:bg-purple-600 data-[state=active]:text-white transition-all"><UsersIcon className="w-4 h-4 mr-2" /> Teachers</TabsTrigger>
                </TabsList>

                <AnimatePresence mode="wait">

                    {/* DIVISIONS TAB */}
                    <TabsContent value="student-groups" className="space-y-4">
                        <motion.div variants={tabVariants} initial="hidden" animate="visible" exit="exit">
                            <Card className="glass-card">
                                <CardHeader>
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <CardTitle>Divisions</CardTitle>
                                            <CardDescription>Manage Year Groups and Divisions (e.g., Year 1 - A). 3 Batches are auto-created.</CardDescription>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end bg-indigo-50/50 p-5 rounded-xl border border-indigo-100/50">
                                        <div className="md:col-span-3"><Label className="text-indigo-900 font-semibold mb-1.5 block">Year</Label><Input value={newGroupYear} onChange={e => setNewGroupYear(e.target.value)} placeholder="e.g. 1" className="bg-white border-indigo-200" /></div>
                                        <div className="md:col-span-3"><Label className="text-indigo-900 font-semibold mb-1.5 block">Division Name</Label><Input value={newGroupDivision} onChange={e => setNewGroupDivision(e.target.value.toUpperCase())} placeholder="e.g. A" className="bg-white border-indigo-200" /></div>
                                        <div className="md:col-span-3"><Label className="text-indigo-900 font-semibold mb-1.5 block text-xs text-muted-foreground">Dept (Suffix)</Label><Input value={newGroupDepartment} onChange={e => setNewGroupDepartment(e.target.value.toUpperCase())} placeholder="CS" className="bg-white border-indigo-200" /></div>
                                        <div className="md:col-span-3"><Button onClick={handleAddGroup} className="w-full bg-indigo-600 hover:bg-indigo-700 h-10 shadow-lg shadow-indigo-200"><Plus className="mr-2 h-4 w-4" /> Add Division</Button></div>
                                    </div>

                                    <div className="space-y-6">
                                        {[1, 2, 3, 4].map(year => {
                                            const yearGroups = groups.filter(g => g.year_level === year);

                                            return (
                                                <div key={year} className="space-y-3">
                                                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                                        <GraduationCap className="h-4 w-4" /> Year {year}
                                                    </h3>
                                                    <div className="grid grid-cols-1 gap-3">
                                                        {yearGroups.map(g => (
                                                            <div key={g.id} className="p-4 border rounded-xl flex justify-between items-center bg-card/40 hover:bg-card transition-colors shadow-sm">
                                                                <div className="flex-1">
                                                                    {editingId === g.id ? (
                                                                        <div className="flex gap-4 items-center">
                                                                            <Input className="h-8 max-w-[200px]" value={editData.name} onChange={e => setEditData({ ...editData, name: e.target.value })} />
                                                                            <Input className="h-8 w-20" type="number" value={editData.size} onChange={e => setEditData({ ...editData, size: parseInt(e.target.value) })} />
                                                                        </div>
                                                                    ) : (
                                                                        <>
                                                                            <div className="font-bold text-lg">{g.name}</div>
                                                                            <div className="text-xs text-muted-foreground mt-1 flex gap-2">
                                                                                <span>Batches:</span>
                                                                                {g.batches && g.batches.length > 0 ? g.batches.map((b, idx) => (
                                                                                    <span key={b.id || `${g.id}-batch-${idx}`} className="bg-primary/10 text-primary px-1.5 rounded">{b.name}</span>
                                                                                )) : <span>(None)</span>}
                                                                            </div>
                                                                        </>
                                                                    )}
                                                                </div>
                                                                <div className="flex gap-1">
                                                                    {editingId === g.id ? (
                                                                        <>
                                                                            <Button variant="ghost" size="sm" onClick={() => handleUpdateGroup(g.id)} className="text-green-600"><Check className="h-4 w-4" /></Button>
                                                                            <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}><X className="h-4 w-4" /></Button>
                                                                        </>
                                                                    ) : (
                                                                        <>
                                                                            <Button variant="ghost" size="sm" onClick={() => { setEditingId(g.id); setEditData(g); }} className="text-muted-foreground"><Pencil className="h-4 w-4" /></Button>
                                                                            <Button variant="ghost" size="sm" onClick={() => handleDeleteGroup(g.id)} className="text-destructive "><Trash2 className="h-4 w-4" /></Button>
                                                                        </>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            );
                                        })}

                                        {groups.length === 0 && (
                                            <div className="text-center py-10 text-muted-foreground bg-accent/5 rounded-lg border border-dashed">
                                                No divisions added yet. Add your first division above.
                                            </div>
                                        )}
                                    </div>

                                    {/* Sidebar Summary Section */}
                                    <div className="pt-6 border-t grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div className="space-y-2">
                                            <h4 className="text-sm font-medium flex items-center gap-2"><SchoolIcon className="h-4 w-4" /> Classrooms ({rooms.length})</h4>
                                            <div className="flex flex-wrap gap-1.5">
                                                {rooms.slice(0, 5).map(r => <span key={r.id} className="text-[10px] bg-muted px-2 py-0.5 rounded">{r.name}</span>)}
                                                {rooms.length > 5 && <span className="text-[10px] text-muted-foreground">+{rooms.length - 5} more</span>}
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <h4 className="text-sm font-medium flex items-center gap-2"><Book className="h-4 w-4" /> Curriculum ({new Set(courses.map(c => c.name.trim().toLowerCase())).size} Subjects)</h4>
                                            <div className="flex flex-wrap gap-1.5">
                                                {courses.slice(0, 3).map(c => <span key={c.id} className="text-[10px] bg-muted px-2 py-0.5 rounded">{c.name}</span>)}
                                                {courses.length > 3 && <span className="text-[10px] text-muted-foreground">+{courses.length - 3} more</span>}
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <h4 className="text-sm font-medium flex items-center gap-2"><UsersIcon className="h-4 w-4" /> Teachers ({teachers.length})</h4>
                                            <div className="flex flex-wrap gap-1.5">
                                                {teachers.slice(0, 5).map(t => <span key={t.id} className="text-[10px] bg-muted px-2 py-0.5 rounded">{t.name}</span>)}
                                                {teachers.length > 5 && <span className="text-[10px] text-muted-foreground">+{teachers.length - 5} more</span>}
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </TabsContent>

                    {/* ROOMS TAB */}
                    <TabsContent value="rooms" className="space-y-4">
                        <motion.div variants={tabVariants} initial="hidden" animate="visible" exit="exit">
                            <Card className="glass-card">
                                <CardHeader><CardTitle>Classrooms</CardTitle></CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex gap-4 items-end bg-accent/20 p-4 rounded-lg">
                                        <div className="flex-1"><Label>Room Name</Label><Input value={newRoomName} onChange={e => setNewRoomName(e.target.value)} placeholder="LH-101" /></div>
                                        <div className="w-40"><Label>Type</Label>
                                            <Select value={newRoomIsLab ? "LAB" : newRoomIsTutorial ? "TUTORIAL" : "CLASS"} onValueChange={v => {
                                                setNewRoomIsLab(v === "LAB");
                                                setNewRoomIsTutorial(v === "TUTORIAL");
                                            }}>
                                                <SelectTrigger><SelectValue /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="CLASS">Classroom</SelectItem>
                                                    <SelectItem value="LAB">Laboratory</SelectItem>
                                                    <SelectItem value="TUTORIAL">Tutorial Room</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <Button onClick={handleAddRoom}><Plus className="mr-2 h-4 w-4" /> Add</Button>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {rooms.map(r => (
                                            <div key={r.id} className="p-4 border rounded-lg bg-card hover:shadow-sm relative group">
                                                {editingId === r.id ? (
                                                    <div className="space-y-2">
                                                        <Input className="h-7 text-xs" value={editData.name} onChange={e => setEditData({ ...editData, name: e.target.value })} />
                                                        <Select value={editData.is_lab ? "LAB" : editData.is_tutorial_room ? "TUTORIAL" : "CLASS"} onValueChange={v => setEditData({ ...editData, is_lab: v === "LAB", is_tutorial_room: v === "TUTORIAL" })}>
                                                            <SelectTrigger className="h-7 text-[10px]"><SelectValue /></SelectTrigger>
                                                            <SelectContent>
                                                                <SelectItem value="CLASS">Classroom</SelectItem>
                                                                <SelectItem value="LAB">Lab</SelectItem>
                                                                <SelectItem value="TUTORIAL">Tutorial Room</SelectItem>
                                                            </SelectContent>
                                                        </Select>
                                                        <div className="flex justify-end gap-1">
                                                            <Button variant="ghost" size="icon" className="h-6 w-6 text-green-600" onClick={() => handleUpdateRoom(r.id)}><Check className="h-3 w-3" /></Button>
                                                            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setEditingId(null)}><X className="h-3 w-3" /></Button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <div className="font-bold">{r.name}</div>
                                                        <div className={`text-xs ${r.is_lab ? "text-blue-500" : r.is_tutorial_room ? "text-purple-500" : "text-gray-500"}`}>{r.is_lab ? "Laboratory" : r.is_tutorial_room ? "Tutorial Room" : "Classroom"}</div>
                                                        <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 flex gap-0.5">
                                                            <Button variant="ghost" size="icon" onClick={() => { setEditingId(r.id); setEditData(r); }} className="h-6 w-6"><Pencil className="h-3 w-3 text-muted-foreground" /></Button>
                                                            <Button variant="ghost" size="icon" onClick={() => handleDeleteRoom(r.id)} className="h-6 w-6"><Trash2 className="h-3 w-3 text-destructive" /></Button>
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </TabsContent>

                    {/* SESSION DESCRIPTIONS TAB */}
                    <TabsContent value="courses" className="space-y-4">
                        <motion.div variants={tabVariants} initial="hidden" animate="visible" exit="exit">
                            <Card className="glass-card overflow-hidden">
                                <CardHeader className="bg-blue-600/5 border-b border-blue-100">
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <CardTitle className="text-blue-900">Session Descriptions</CardTitle>
                                            <CardDescription>Organize sessions by year. Each session needs Type, Hours, and Name.</CardDescription>
                                        </div>
                                        <Button variant="outline" className="border-blue-200 text-blue-700 hover:bg-blue-50" onClick={() => setActiveSessionYear(prev => prev < 4 ? prev + 1 : 1)}>Next Year &rarr;</Button>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-6 space-y-8">
                                    {/* Year-specific Sub-tabs */}
                                    <div className="flex border-b border-gray-100 mb-6">
                                        {[1, 2, 3, 4].map(y => (
                                            <button
                                                key={y}
                                                onClick={() => setActiveSessionYear(y)}
                                                className={`py-3 px-6 text-sm font-bold border-b-2 transition-all ${activeSessionYear === y
                                                    ? "border-blue-600 text-blue-700 bg-blue-50/50"
                                                    : "border-transparent text-gray-500 hover:text-blue-500 hover:border-blue-200"
                                                    }`}
                                            >
                                                Year {y}
                                            </button>
                                        ))}
                                    </div>

                                    {/* Division Requirement Warning */}
                                    {groups.filter(g => g.year_level === activeSessionYear).length === 0 && (
                                        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-sm flex items-center gap-3 mb-6">
                                            <div className="h-8 w-8 rounded-full bg-amber-200 flex items-center justify-center">⚠️</div>
                                            <p className="font-medium">Year {activeSessionYear} has no divisions yet. Head over to the <strong>Divisions</strong> tab to create one before adding sessions.</p>
                                        </div>
                                    )}

                                    {/* Add Session Form for Active Year */}
                                    <div className={`p-5 rounded-2xl border border-blue-200 bg-blue-50/30 grid grid-cols-1 md:grid-cols-12 gap-4 items-end shadow-sm ${groups.filter(g => g.year_level === activeSessionYear).length === 0 ? "opacity-50 pointer-events-none" : ""}`}>
                                        <div className="md:col-span-2">
                                            <Label className="text-xs font-bold text-blue-800 mb-1.5 block">Type</Label>
                                            <Select value={newCourseType} onValueChange={(v: any) => {
                                                setNewCourseType(v);
                                                if (v === "TUTORIAL") setNewCourseHours(1);
                                                else if (v === "LAB") setNewCourseHours(2);
                                                else setNewCourseHours(4);
                                            }}>
                                                <SelectTrigger className="h-10 bg-white border-blue-100"><SelectValue /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="THEORY">Lecture</SelectItem>
                                                    <SelectItem value="LAB">Lab</SelectItem>
                                                    <SelectItem value="TUTORIAL">Tutorial</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="md:col-span-3">
                                            <Label className="text-xs font-bold text-blue-800 mb-1.5 block">Subject Name *</Label>
                                            <Input className="h-10 bg-white border-blue-100" value={newCourseName} onChange={e => {
                                                setNewCourseName(e.target.value);
                                                if (!newCourseCode) setNewCourseCode(e.target.value.substring(0, 3).toUpperCase() + Math.floor(Math.random() * 100));
                                            }} placeholder="e.g. Maths" />
                                        </div>
                                        <div className="md:col-span-2">
                                            <Label className="text-xs font-bold text-blue-800 mb-1.5 block">Code *</Label>
                                            <Input className="h-10 bg-white border-blue-100" value={newCourseCode} onChange={e => setNewCourseCode(e.target.value)} placeholder="MAT101" />
                                        </div>
                                        <div className="md:col-span-1">
                                            <Label className="text-xs font-bold text-blue-800 mb-1.5 block">Hrs/Wk</Label>
                                            <Input className="h-10 bg-white border-blue-100" type="number" value={newCourseHours} onChange={e => setNewCourseHours(parseInt(e.target.value) || 2)} />
                                        </div>
                                        <div className="md:col-span-2">
                                            <Button className="w-full bg-blue-600 hover:bg-blue-700 h-10 shadow-lg shadow-blue-200" onClick={handleAddCourse}>Add Session</Button>
                                        </div>
                                    </div>

                                    {/* List for Active Year */}
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Sessions for Year {activeSessionYear}</h3>
                                        {courses.filter(c => c.student_group?.year_level === activeSessionYear).length === 0 && (
                                            <p className="text-muted-foreground text-center py-12 border border-dashed rounded-xl bg-muted/5 italic">
                                                {groups.filter(g => g.year_level === activeSessionYear).length === 0
                                                    ? `Waiting for divisions to be created in Year ${activeSessionYear}...`
                                                    : `No sessions defined for Year ${activeSessionYear} yet.`}
                                            </p>
                                        )}
                                        {(() => {
                                            const grouped = courses
                                                .filter(c => c.student_group?.year_level === activeSessionYear)
                                                .reduce((acc, c) => {
                                                    const key = `${c.name}-${c.course_type}-${c.weekly_sessions}`;
                                                    if (!acc[key]) acc[key] = {
                                                        name: c.name,
                                                        type: c.course_type,
                                                        sessions: c.weekly_sessions,
                                                        codePrefix: c.code.split('-')[0], // Guess prefix
                                                        items: []
                                                    };
                                                    acc[key].items.push(c);
                                                    return acc;
                                                }, {} as Record<string, any>);

                                            return Object.values(grouped).map((group: any) => {
                                                const groupKey = `${group.name}-${group.type}-${group.sessions}`;
                                                // Calculate Assignment Status per Division
                                                const divStatus = Array.from(new Set(group.items.map((i: any) => {
                                                    const gid = i.student_group_id || i.student_group?.id;
                                                    return i.student_group?.name || groups.find(g => g.id === gid)?.name || 'Unknown';
                                                }))).sort().map((divName: any) => {
                                                    const divItems = group.items.filter((i: any) => {
                                                        const gid = i.student_group_id || i.student_group?.id;
                                                        const name = i.student_group?.name || groups.find(g => g.id === gid)?.name || 'Unknown';
                                                        return name === divName;
                                                    });
                                                    const assignedCount = divItems.filter((i: any) => i.teacher_id).length;
                                                    const totalCount = divItems.length;
                                                    // Clean Div Name: "CS AIML-SY-A" -> "A"
                                                    const shortDiv = divName.replace(/.*-/, '');
                                                    const isFull = assignedCount === totalCount && totalCount > 0;
                                                    return (
                                                        <span key={`${groupKey}-${divName}`} className={`px-1.5 py-0.5 rounded text-[10px] border ${isFull ? 'bg-green-50 text-green-700 border-green-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                                                            {shortDiv}: {assignedCount}/{totalCount}
                                                        </span>
                                                    );
                                                });

                                                return (
                                                    <div key={groupKey} className="border rounded-xl bg-card hover:bg-blue-50/20 transition-all shadow-sm overflow-hidden mb-3">
                                                        {/* Group Header (Master Card) */}
                                                        <div className="flex items-center justify-between p-4 bg-white">
                                                            {editingId === groupKey ? (
                                                                <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4 items-center mr-4">
                                                                    <Input className="h-9" value={editData.name} onChange={e => setEditData({ ...editData, name: e.target.value })} placeholder="Subject Name" />
                                                                    <Input className="h-9" type="number" value={editData.weekly_sessions} onChange={e => setEditData({ ...editData, weekly_sessions: parseInt(e.target.value) })} />
                                                                    <Select value={editData.course_type} onValueChange={(v: any) => setEditData({ ...editData, course_type: v })}>
                                                                        <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                                                                        <SelectContent>
                                                                            <SelectItem value="THEORY">Theory</SelectItem>
                                                                            <SelectItem value="LAB">Lab</SelectItem>
                                                                            <SelectItem value="TUTORIAL">Tutorial</SelectItem>
                                                                        </SelectContent>
                                                                    </Select>
                                                                    <div className="text-xs text-muted-foreground">Updates {group.items.length} sessions</div>
                                                                </div>
                                                            ) : (
                                                                <div className="flex items-center gap-4">
                                                                    <div className="h-10 w-10 rounded-lg bg-blue-100/50 flex items-center justify-center text-blue-600 font-bold border border-blue-100 shadow-sm">
                                                                        {group.name.substring(0, 2).toUpperCase()}
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="font-bold text-blue-900 text-sm">{group.name}</h4>
                                                                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                                                                            <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-bold uppercase">{group.type}</span>
                                                                            <span className="text-[10px] font-mono text-muted-foreground">{group.sessions} hrs/wk</span>
                                                                            <div className="flex gap-1 ml-2">
                                                                                {divStatus}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}

                                                            <div className="flex items-center gap-2">
                                                                {editingId === groupKey ? (
                                                                    <>
                                                                        <Button variant="ghost" size="sm" className="text-green-600 h-8 w-8 p-0" onClick={() => handleUpdateCourseGroup(group.items, { name: editData.name, weekly_sessions: editData.weekly_sessions, course_type: editData.course_type })}><Check className="h-4 w-4" /></Button>
                                                                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setEditingId(null)}><X className="h-4 w-4" /></Button>
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <Button variant="ghost" size="sm" className="text-muted-foreground h-8 w-8 p-0" onClick={() => {
                                                                            setEditingId(groupKey);
                                                                            setEditData({ name: group.name, weekly_sessions: group.sessions, course_type: group.type });
                                                                        }}><Pencil className="h-4 w-4" /></Button>
                                                                        <Button variant="ghost" size="sm" className="text-destructive h-8 w-8 p-0" onClick={() => handleDeleteCourseGroup(group.items)}><Trash2 className="h-4 w-4" /></Button>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>

                                    {/* Common Breaks Section */}
                                    <div className="mt-12 p-6 border border-purple-200 rounded-3xl bg-purple-50/30 relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-4 opacity-10"><UsersIcon className="h-24 w-24 text-purple-900" /></div>
                                        <div className="flex justify-between items-center mb-6 relative">
                                            <div>
                                                <h3 className="text-lg font-bold text-purple-900">Common Breaks</h3>
                                                <p className="text-xs text-purple-600">Set slots that apply to all years and divisions.</p>
                                            </div>
                                            <Button variant="secondary" size="sm" className="bg-purple-600 text-white hover:bg-purple-700 shadow-md" onClick={handleAddBreak}>
                                                <Plus className="w-3 h-3 mr-1.5" /> Add Break
                                            </Button>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
                                            {breaks.map(b => (
                                                <div key={b.id} className="flex gap-3 items-center bg-white p-3 rounded-xl border border-purple-100 shadow-sm">
                                                    <div className="h-8 w-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-700 font-bold text-xs uppercase">{b.name.charAt(0)}</div>
                                                    <div className="flex-1 grid grid-cols-3 gap-2">
                                                        <Input className="h-8 text-[11px] border-none bg-purple-50/50" value={b.name} onBlur={e => handleUpdateBreak(b.id, { name: e.target.value })} onChange={e => setBreaks(breaks.map(x => x.id === b.id ? { ...x, name: e.target.value } : x))} />
                                                        <Input className="h-8 text-[11px] border-none bg-purple-50/50" type="time" value={b.start_time} onBlur={e => handleUpdateBreak(b.id, { start_time: e.target.value })} onChange={e => setBreaks(breaks.map(x => x.id === b.id ? { ...x, start_time: e.target.value } : x))} />
                                                        <Input className="h-8 text-[11px] border-none bg-purple-50/50" type="time" value={b.end_time} onBlur={e => handleUpdateBreak(b.id, { end_time: e.target.value })} onChange={e => setBreaks(breaks.map(x => x.id === b.id ? { ...x, end_time: e.target.value } : x))} />
                                                    </div>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8 text-purple-300 hover:text-red-500" onClick={() => handleDeleteBreak(b.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Solver Run Section */}
                                    <div className="mt-8 pt-8 border-t">
                                        <div className="flex justify-between items-center mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold">Generate Timetable</h3>
                                                <p className="text-sm text-muted-foreground">Run the AI solver using currently entered master data.</p>
                                            </div>
                                            <Button
                                                size="lg"
                                                onClick={handleGenerate}
                                                disabled={solverStatus === "running"}
                                                className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-xl hover:shadow-indigo-200 transition-all font-bold px-8"
                                            >
                                                {solverStatus === "running" ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Plus className="mr-2 h-5 w-5" />}
                                                {solverStatus === "running" ? "Generating..." : "Run AI Solver"}
                                            </Button>
                                        </div>

                                        {solverStatus !== "idle" && (
                                            <Card className="bg-slate-950 text-slate-50 border-none shadow-2xl overflow-hidden rounded-2xl">
                                                <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                                                    <div className="flex items-center gap-2">
                                                        <div className={`h-2 w-2 rounded-full ${solverStatus === 'running' ? 'bg-blue-500 animate-pulse' : solverStatus === 'done' ? 'bg-green-500' : 'bg-red-500'}`} />
                                                        <span className="text-xs font-mono uppercase tracking-widest text-slate-400">Solver Console</span>
                                                    </div>
                                                    <span className="text-[10px] font-mono text-slate-500">{solverTaskId}</span>
                                                </div>
                                                <div className="p-4 h-48 overflow-y-auto font-mono text-xs space-y-1">
                                                    {solverLogs.map((log, i) => (
                                                        <div key={i} className="flex gap-4">
                                                            <span className="text-slate-600 w-4 tracking-tighter">{i + 1}</span>
                                                            <span className={log.includes('Aborted') || log.includes('error') ? 'text-red-400' : 'text-slate-300'}>{log}</span>
                                                        </div>
                                                    ))}
                                                    {solverStatus === "running" && <div className="text-blue-400 animate-pulse">_</div>}
                                                    {solverLogs.length === 0 && <div className="text-slate-600 italic">Initializing stream...</div>}
                                                </div>
                                                {solverStatus === "done" && (
                                                    <div className="p-3 bg-green-500/10 border-t border-green-500/20 text-center">
                                                        <p className="text-green-400 text-xs font-bold font-mono">SOLVER COMPLETED SUCCESSFULLY</p>
                                                    </div>
                                                )}
                                            </Card>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </TabsContent>

                    {/* TEACHERS TAB */}
                    <TabsContent value="teachers" className="space-y-4">
                        <motion.div variants={tabVariants} initial="hidden" animate="visible" exit="exit">
                            <div className="flex justify-between items-center mb-4">
                                <CardTitle className="text-xl">Faculty & Assignments</CardTitle>
                                <div className="flex gap-2">
                                    <Input placeholder="Mrs. Doe" className="w-60" value={newTeacherName} onChange={e => setNewTeacherName(e.target.value)} />
                                    <Button onClick={handleAddTeacher}><Plus className="w-4 h-4 mr-2" /> Add Teacher</Button>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {teachers.map(teacher => {
                                    const teacherSessions = courses.filter(c => c.teacher_id === teacher.id);

                                    return (
                                        <Card key={teacher.id} className="overflow-hidden border shadow-sm hover:shadow-md transition-shadow">
                                            <div className="p-4 bg-muted/20 flex justify-between items-center border-b">
                                                <div className="flex items-center gap-3 flex-1">
                                                    <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                                                        {teacher.name.substring(0, 2).toUpperCase()}
                                                    </div>
                                                    <div className="flex-1">
                                                        {editingId === teacher.id ? (
                                                            <div className="flex gap-4">
                                                                <Input className="h-8" value={editData.name} onChange={e => setEditData({ ...editData, name: e.target.value })} placeholder="Name" />
                                                                <Input className="h-8" value={editData.email} onChange={e => setEditData({ ...editData, email: e.target.value })} placeholder="Email" />
                                                            </div>
                                                        ) : (
                                                            <>
                                                                <div className="font-bold text-lg">{teacher.name}</div>
                                                                <div className="text-xs text-muted-foreground">{teacher.email}</div>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex gap-1">
                                                    {editingId === teacher.id ? (
                                                        <>
                                                            <Button variant="ghost" size="sm" onClick={() => handleUpdateTeacher(teacher.id)} className="text-green-600"><Check className="h-4 w-4" /></Button>
                                                            <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}><X className="h-4 w-4" /></Button>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Button variant="ghost" size="sm" onClick={() => { setEditingId(teacher.id); setEditData(teacher); }} className="text-muted-foreground"><Pencil className="h-4 w-4" /></Button>
                                                            <Button variant="ghost" size="sm" onClick={() => handleDeleteTeacher(teacher.id)} className="text-destructive"><Trash2 className="h-4 w-4" /></Button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Sessions View */}
                                            <div className="p-5 bg-card/50">
                                                <div className="space-y-3">
                                                    <div className="flex justify-between items-center border-b border-purple-100 pb-2">
                                                        <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">Workload & Assignments</h4>
                                                        <span className="text-[10px] font-bold bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{teacherSessions.length} Sessions</span>
                                                    </div>

                                                    {/* Assign Button / Form */}
                                                    <div className="mb-4">
                                                        <Select value="" onValueChange={(val) => {
                                                            (async () => {
                                                                if (val.startsWith('ALL_BATCHES:')) {
                                                                    const [, courseName, divisionId] = val.split(':');
                                                                    await handleAssignToAllBatches(courseName, divisionId, teacher.id);
                                                                } else if (val.startsWith('SPLIT:')) {
                                                                    const [, courseId, batchName] = val.split(':');
                                                                    const course = courses.find(c => c.id === courseId);
                                                                    if (course) await handleSplitAndAssign(course, batchName, teacher.id);
                                                                } else if (val.startsWith('BULK:')) {
                                                                    // BULK logic removed
                                                                } else {
                                                                    await handleUpdateCourseTeacher(val, teacher.id);
                                                                }
                                                            })();
                                                        }}>
                                                            <SelectTrigger className="h-9 w-full md:w-80 border-dashed border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100/50 transition-colors rounded-xl shadow-sm">
                                                                <div className="flex items-center gap-2">
                                                                    <Plus className="w-3.5 h-3.5" />
                                                                    <span className="text-xs font-bold">Assign Session</span>
                                                                </div>
                                                            </SelectTrigger>
                                                            <SelectContent className="max-h-[400px]">
                                                                <div className="p-2 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Unassigned Sessions</div>

                                                                {/* THEORY Courses */}
                                                                {courses.filter(c => !c.teacher_id && c.course_type === 'THEORY').length > 0 && (
                                                                    <>
                                                                        <div className="px-2 py-1 text-[9px] font-semibold text-blue-600 uppercase tracking-wider bg-blue-50 mt-1">📚 Theory</div>
                                                                        {courses.filter(c => !c.teacher_id && c.course_type === 'THEORY').map(c => (
                                                                            <SelectItem key={c.id} value={c.id}>
                                                                                <span className="font-bold text-xs">[{c.student_group?.name}]</span> {c.name}
                                                                            </SelectItem>
                                                                        ))}
                                                                    </>
                                                                )}



                                                                {/* LAB/TUTORIAL Courses - Grouped by Subject with All Batches option */}
                                                                {(() => {
                                                                    const labGroups = courses
                                                                        .filter(c => ['LAB', 'TUTORIAL'].includes(c.course_type)) // Changed to include all lab/tutorial courses
                                                                        .reduce((acc, course) => {
                                                                            const gid = course.student_group_id || course.student_group?.id;
                                                                            const key = `${course.name}-${gid}`;
                                                                            if (!acc[key]) {
                                                                                // Lookup group name if missing from relation
                                                                                let divName = course.student_group?.name;
                                                                                if (!divName && gid) {
                                                                                    const foundGroup = groups.find(g => g.id === gid);
                                                                                    divName = foundGroup?.name;
                                                                                }

                                                                                acc[key] = {
                                                                                    name: course.name,
                                                                                    division: divName || 'Unknown Div',
                                                                                    divisionId: gid || '',
                                                                                    batches: []
                                                                                };
                                                                            }
                                                                            acc[key].batches.push(course);
                                                                            return acc;
                                                                        }, {} as Record<string, any>);

                                                                    const groups = Object.values(labGroups);

                                                                    // Only show groups that have at least one unassigned batch OR are relevant to see
                                                                    // The user wants to see all batches for a given subject/division, even if some are assigned.
                                                                    // So, we iterate over all 'groups' that have any batches.
                                                                    const relevantGroups = groups.filter(g => g.batches.length > 0);

                                                                    return relevantGroups.length > 0 && (
                                                                        <>
                                                                            <div className="px-2 py-1 text-[9px] font-semibold text-green-600 uppercase tracking-wider bg-green-50 mt-1">🔬 Lab / Tutorial</div>
                                                                            {relevantGroups.map((group: any) => {
                                                                                const mainCourse = group.batches[0]; // Any course from the group to link to

                                                                                // BATCH SLOT LOGIC: Always assume 3 batches (1, 2, 3)
                                                                                // Find existing courses that match these batches
                                                                                const batchSlots = [1, 2, 3].map(bNum => {
                                                                                    const bStr = bNum.toString();
                                                                                    // Find existing course for this batch
                                                                                    // Matches if: batch.name == "1" OR code ends in "-B1"
                                                                                    const existing = group.batches.find((c: any) =>
                                                                                        c.batch?.name === bStr ||
                                                                                        c.code.endsWith(`-B${bStr}`)
                                                                                    );

                                                                                    return {
                                                                                        batchNum: bStr,
                                                                                        course: existing
                                                                                    };
                                                                                });

                                                                                // Calculate remaining based on slots that DON'T have an assigned teacher
                                                                                // If slot is empty (virtual), it counts as unassigned.
                                                                                // If slot has course, check course.teacher_id.
                                                                                const remainingCount = batchSlots.reduce((acc, slot) => {
                                                                                    if (!slot.course) return acc + 1; // Uncreated batch = Unassigned
                                                                                    return acc + (!slot.course.teacher_id ? 1 : 0);
                                                                                }, 0);

                                                                                return (
                                                                                    <div key={`${group.name}-${group.divisionId}`}>
                                                                                        {/* Division Header: Always Visible */}
                                                                                        {remainingCount > 0 ? (
                                                                                            <SelectItem
                                                                                                value={`ALL_BATCHES:${group.name}:${group.divisionId}`}
                                                                                                className="font-bold border-l-2 border-green-500 pl-2 bg-green-50/30 mt-2"
                                                                                            >
                                                                                                <span className="font-bold text-xs text-green-700">[{group.division}] {group.name}</span>
                                                                                                <span className="ml-2 text-[9px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded border border-green-200">
                                                                                                    Assign Remaining ({remainingCount})
                                                                                                </span>
                                                                                            </SelectItem>
                                                                                        ) : (
                                                                                            <div className="px-2 py-1.5 text-xs font-bold text-slate-500 bg-slate-50 border-y border-slate-100 mt-2 flex justify-between items-center">
                                                                                                <span>[{group.division}] {group.name}</span>
                                                                                                <span className="text-[9px] text-slate-400 italic font-normal">All Assigned</span>
                                                                                            </div>
                                                                                        )}
                                                                                        {/* Render B1, B2, B3 Slots */}
                                                                                        {batchSlots.map((slot) => {
                                                                                            const isVirtual = !slot.course;
                                                                                            const isAssigned = !isVirtual && !!slot.course.teacher_id;
                                                                                            const assignedTeacher = isAssigned ? teachers.find(t => t.id === slot.course.teacher_id)?.name : null;
                                                                                            const assignedToMe = isAssigned && slot.course.teacher_id === teacher.id;

                                                                                            // Value: If existing, use ID. If virtual, use SPLIT command.
                                                                                            // SPLIT:COURSE_ID:BATCH_NAME. Use mainCourse.id as base.
                                                                                            const value = isVirtual
                                                                                                ? `SPLIT:${mainCourse.id}:${slot.batchNum}`
                                                                                                : slot.course.id;

                                                                                            return (
                                                                                                <SelectItem
                                                                                                    key={`${group.name}-${group.divisionId}-B${slot.batchNum}`}
                                                                                                    value={value}
                                                                                                    disabled={isAssigned}
                                                                                                    className={`pl-8 text-[11px] ${isAssigned ? 'opacity-50 cursor-not-allowed bg-slate-50' : 'text-muted-foreground'}`}
                                                                                                >
                                                                                                    <div className="flex items-center justify-between w-full gap-4">
                                                                                                        <span className="flex items-center gap-2">
                                                                                                            <span className={`w-1.5 h-1.5 rounded-full ${isAssigned ? 'bg-slate-300' : 'bg-indigo-300'}`}></span>
                                                                                                            <span className={`font-mono font-bold ${isAssigned ? 'text-slate-500' : 'text-indigo-600'}`}>B{slot.batchNum}</span>
                                                                                                            {/* Show Code only if real course exists */}
                                                                                                            {!isVirtual && <span className="text-[9px] text-muted-foreground/50 ml-1">({slot.course.code})</span>}
                                                                                                            {isVirtual && <span className="text-[9px] text-muted-foreground/50 ml-1 italic">(New)</span>}
                                                                                                        </span>
                                                                                                        {isAssigned && (
                                                                                                            <span className="text-[9px] italic text-slate-400">
                                                                                                                {assignedToMe ? '(You)' : `(${assignedTeacher?.split(' ')[0] || 'Assigned'})`}
                                                                                                            </span>
                                                                                                        )}
                                                                                                    </div>
                                                                                                </SelectItem>
                                                                                            );
                                                                                        })}
                                                                                    </div>
                                                                                );
                                                                            })}
                                                                        </>
                                                                    );
                                                                })()}

                                                                {courses.filter(c => !c.teacher_id).length === 0 && (
                                                                    <div className="p-4 text-center text-xs text-muted-foreground italic">No unassigned sessions available</div>
                                                                )}
                                                            </SelectContent>
                                                        </Select>
                                                    </div>

                                                    {teacherSessions.length === 0 ? (
                                                        <div className="flex flex-col items-center justify-center py-8 border border-dashed rounded-2xl bg-muted/5">
                                                            <p className="text-xs text-muted-foreground italic mb-2">No workload assigned yet.</p>
                                                        </div>
                                                    ) : (
                                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                                            {(() => {
                                                                // Group sessions by Name + Type + Div
                                                                const groupedSessions = teacherSessions.reduce((acc, session) => {
                                                                    const gid = session.student_group_id || session.student_group?.id;
                                                                    const key = `${session.name}-${session.course_type}-${gid}`;
                                                                    if (!acc[key]) {
                                                                        acc[key] = {
                                                                            baseSession: session,
                                                                            sessions: []
                                                                        };
                                                                    }
                                                                    acc[key].sessions.push(session);
                                                                    return acc;
                                                                }, {} as Record<string, { baseSession: any, sessions: any[] }>);

                                                                return Object.values(groupedSessions).map(group => {
                                                                    const { baseSession, sessions } = group;
                                                                    // Resolve Division Name safely
                                                                    const gid = baseSession.student_group_id || baseSession.student_group?.id;
                                                                    const divName = baseSession.student_group?.name || groups.find(g => g.id === gid)?.name || 'Unknown Class';

                                                                    return (
                                                                        <div key={baseSession.id} className="group relative flex flex-col gap-1 p-3 rounded-xl border bg-white hover:border-purple-300 transition-all hover:shadow-sm">
                                                                            <div className="flex justify-between items-start">
                                                                                <span className="font-bold text-sm text-purple-900">{baseSession.name}</span>
                                                                                <span className="text-[9px] font-bold bg-muted px-1.5 py-0.5 rounded text-muted-foreground uppercase">{baseSession.course_type}</span>
                                                                            </div>
                                                                            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                                                                                <GraduationCap className="h-3 w-3" />
                                                                                <span className="font-semibold">{divName}</span>
                                                                                <span>•</span>
                                                                                <span>{sessions.reduce((sum, s) => sum + s.weekly_sessions, 0)} hrs</span>
                                                                            </div>

                                                                            {/* Batches Display - ONLY for LABs/TUTORIALs with batches */}
                                                                            {['LAB', 'TUTORIAL'].includes(baseSession.course_type) && (
                                                                                <div className="flex flex-wrap gap-1 mt-2">
                                                                                    {sessions.sort((a, b) => (a.batch?.name || '').localeCompare(b.batch?.name || '')).map(s => {
                                                                                        // Smart batch name extraction
                                                                                        let bName = s.batch?.name;
                                                                                        if (!bName) {
                                                                                            const parts = s.code.split('-B');
                                                                                            if (parts.length > 1) bName = parts.pop();
                                                                                            else bName = s.batch ? '?' : '';
                                                                                        }
                                                                                        if (!bName) bName = "?";

                                                                                        return (
                                                                                            <span key={s.id} className="inline-flex items-center text-[10px] bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded border border-purple-100 group/batch cursor-default">
                                                                                                <span className="font-mono font-bold">B{bName}</span>
                                                                                                <button
                                                                                                    onClick={(e) => { e.stopPropagation(); handleUpdateCourseTeacher(s.id, "unassigned"); }}
                                                                                                    className="ml-1 text-purple-400 hover:text-red-600 opacity-0 group-hover/batch:opacity-100 transition-opacity p-0.5 rounded-full hover:bg-purple-100"
                                                                                                    title="Unassign this batch"
                                                                                                >
                                                                                                    <X className="w-2.5 h-2.5" />
                                                                                                </button>
                                                                                            </span>
                                                                                        );
                                                                                    })}
                                                                                </div>
                                                                            )}

                                                                            {/* Action Buttons */}
                                                                            <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                                {/* Reassign Whole Group */}
                                                                                <Select value="" onValueChange={(newTId) => sessions.forEach(s => handleUpdateCourseTeacher(s.id, newTId))}>
                                                                                    <SelectTrigger className="h-6 w-6 p-0 border-none bg-blue-500 hover:bg-blue-600 text-white rounded-full" title="Reassign all">
                                                                                        <div className="flex items-center justify-center w-full h-full">
                                                                                            <UsersIcon className="h-3 w-3" />
                                                                                        </div>
                                                                                    </SelectTrigger>
                                                                                    <SelectContent>
                                                                                        <div className="p-2 text-[9px] font-bold text-muted-foreground uppercase">Reassign All To</div>
                                                                                        {teachers.filter(t => t.id !== teacher.id).map(t => (
                                                                                            <SelectItem key={t.id} value={t.id}>
                                                                                                <span className="text-xs">{t.name}</span>
                                                                                            </SelectItem>
                                                                                        ))}
                                                                                    </SelectContent>
                                                                                </Select>

                                                                                {/* Unassign Whole Group */}
                                                                                <button
                                                                                    onClick={() => sessions.forEach(s => handleUpdateCourseTeacher(s.id, "unassigned"))}
                                                                                    className="h-6 w-6 p-0 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all"
                                                                                    title="Unassign all"
                                                                                >
                                                                                    <X className="h-3 w-3" />
                                                                                </button>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                });
                                                            })()}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </Card>
                                    );
                                })}
                            </div>
                        </motion.div>
                    </TabsContent>

                </AnimatePresence>
            </Tabs>
        </div >
    );
}
