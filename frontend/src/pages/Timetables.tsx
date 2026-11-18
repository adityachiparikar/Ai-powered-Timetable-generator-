import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import TimetableGrid from "@/components/timetable/TimetableGrid";
import { solverApi } from "@/services/api";
import { Loader2, Calendar, RefreshCcw, Terminal } from "lucide-react";

export default function Timetables() {
    const [generating, setGenerating] = useState(false);
    const [loading, setLoading] = useState(true);
    const [taskId, setTaskId] = useState<string | null>(null);
    const [timetableData, setTimetableData] = useState<any[]>([]);
    const [status, setStatus] = useState<string>("IDLE");
    const [consoleLines, setConsoleLines] = useState<string[]>([]);

    const appendConsole = (...lines: string[]) => {
        setConsoleLines(prev => [...prev, ...lines.filter(Boolean)]);
    };

    const formatError = (e: any) => {
        const detail = e.response?.data?.detail;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) return detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
        return e.message || "Unknown error";
    };

    const fetchSaved = async () => {
        setLoading(true);
        try {
            const res = await solverApi.getSaved("Fall 2025");
            if (res.data && res.data.entries) {
                const mapped = res.data.entries.map((e: any) => ({
                    ...e,
                    time: e.time_range
                }));
                setTimetableData(mapped);
            }
        } catch (e) {
            console.error("Failed to fetch saved timetable", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSaved();
    }, []);

    useEffect(() => {
        const refreshOnTimetableUpdate = () => fetchSaved();
        const refreshOnStorage = (event: StorageEvent) => {
            if (event.key === "timetable_updated_at") fetchSaved();
        };
        const refreshOnVisible = () => {
            if (document.visibilityState === "visible") fetchSaved();
        };

        window.addEventListener("timetable-updated", refreshOnTimetableUpdate);
        window.addEventListener("storage", refreshOnStorage);
        document.addEventListener("visibilitychange", refreshOnVisible);

        return () => {
            window.removeEventListener("timetable-updated", refreshOnTimetableUpdate);
            window.removeEventListener("storage", refreshOnStorage);
            document.removeEventListener("visibilitychange", refreshOnVisible);
        };
    }, []);

    const applyGeneratedEntries = (entries: any[]) => {
        const mapped = entries.map((e: any) => ({
            ...e,
            time: e.time_range
        }));
        setTimetableData(mapped);
    };

    const pollStatus = async (id: string) => {
        try {
            const res = await solverApi.getStatus(id);
            const { status, result } = res.data;
            setStatus(status);
            if (result?.logs) setConsoleLines(result.logs);

            if (status === "SUCCESS") {
                setGenerating(false);
                if (result && ["OPTIMAL", "FEASIBLE"].includes(result.status) && result.entries?.length > 0) {
                    applyGeneratedEntries(result.entries);
                } else {
                    setTimetableData([]);
                    appendConsole(`Solver finished without a timetable. Result status: ${result?.status || "UNKNOWN"}`);
                }
            } else if (status === "FAILURE" || status === "REVOKED") {
                setGenerating(false);
                appendConsole(`Timetable generation failed: ${res.data.error || status}`);
            } else {
                // Still pending or processing
                setTimeout(() => pollStatus(id), 2000);
            }
        } catch (e) {
            console.error(e);
            setGenerating(false);
            appendConsole(`Failed to check solver status: ${formatError(e)}`);
        }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        setTimetableData([]);
        setStatus("STARTING");
        setConsoleLines(["Starting timetable generation..."]);
        try {
            // Load config from localStorage
            let config = null;
            try {
                const stored = localStorage.getItem("solver_config");
                if (stored) config = JSON.parse(stored);
            } catch (e) {
                console.error("Failed to parse solver config", e);
            }
            config = {
                ...(config || {}),
                max_time_seconds: config?.max_time_seconds ?? 90,
                enable_soft_constraints: true,
                minimize_gaps: true,
                max_group_gap_hours: config?.max_group_gap_hours ?? 2,
            };

            const res = await solverApi.generate("Fall 2025", config);
            const newTaskId = res.data.task_id;
            setTaskId(newTaskId);

            if (res.data.status === "SUCCESS" && res.data.result) {
                const result = res.data.result;
                setStatus(result.status || "SUCCESS");
                setGenerating(false);
                setConsoleLines(result.logs || []);
                if (["OPTIMAL", "FEASIBLE"].includes(result.status) && result.entries?.length > 0) {
                    applyGeneratedEntries(result.entries);
                } else {
                    setTimetableData([]);
                    appendConsole(
                        `Solver did not generate a timetable. Result status: ${result.status || "UNKNOWN"}`,
                        result.reason ? `Reason: ${result.reason}` : "",
                        result.status === "UNKNOWN" ? "The solver hit the time limit before finding a feasible schedule. Try increasing max_time_seconds or reducing imported workload." : "",
                    );
                }
                return;
            }

            pollStatus(newTaskId);

        } catch (e: any) {
            console.error(e);
            appendConsole(`Failed to start solver: ${formatError(e)}`);
            setGenerating(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">Timetables</h2>
                    <p className="text-muted-foreground">View and manage generated schedules.</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="icon" onClick={fetchSaved} disabled={loading || generating}>
                        <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                    <Button onClick={handleGenerate} disabled={generating || loading} className="bg-primary hover:bg-primary/90">
                        {generating ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating ({status})...</> : "Generate New"}
                    </Button>
                    <Button variant="outline" onClick={() => {
                        if (timetableData.length === 0) return alert("Generate a timetable first.");
                        const headers = ["Day", "Time", "Course", "Room"];
                        const csvContent = [
                            headers.join(","),
                            ...timetableData.map(r => `${r.day},"${r.time_range}","${r.course_id}","${r.room_id}"`)
                        ].join("\n");

                        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                        const link = document.createElement("a");
                        link.href = URL.createObjectURL(blob);
                        link.download = "timetable_export.csv";
                        link.click();
                    }}>
                        Export CSV
                    </Button>
                </div>
            </div>

            {consoleLines.length > 0 && (
                <div className="rounded-lg border bg-zinc-950 text-zinc-100 shadow-sm overflow-hidden">
                    <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2">
                        <Terminal className="h-4 w-4 text-emerald-400" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Solver Console</span>
                        <span className="ml-auto text-xs text-zinc-500">{status}</span>
                    </div>
                    <div className="max-h-64 overflow-auto p-4 font-mono text-xs leading-5">
                        {consoleLines.map((line, index) => (
                            <div key={`${index}-${line}`} className={line.toLowerCase().includes("warning") || line.toLowerCase().includes("failed") || line.toLowerCase().includes("infeasible") || line.toLowerCase().includes("unknown") ? "text-amber-300" : "text-zinc-300"}>
                                {line}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="min-h-[400px] flex flex-col gap-12">
                {loading && timetableData.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 opacity-50">
                        <Loader2 className="h-10 w-10 animate-spin text-primary" />
                        <p>Loading saved timetable...</p>
                    </div>
                ) : timetableData.length > 0 ? (
                    // Group entries by student_group
                    Object.entries(
                        timetableData.reduce((acc: any, entry: any) => {
                            const group = entry.student_group || "General";
                            if (!acc[group]) acc[group] = [];
                            acc[group].push(entry);
                            return acc;
                        }, {})
                    ).map(([groupName, groupEntries]: [string, any]) => (
                        <div key={groupName} className="space-y-4">
                            <div className="flex items-center gap-3 px-2">
                                <div className="h-8 w-1 bg-primary rounded-full" />
                                <h3 className="text-xl font-bold text-gray-800 dark:text-zinc-100">
                                    Division: {groupName}
                                </h3>
                            </div>
                            <div className="border border-gray-200 dark:border-zinc-800 rounded-2xl overflow-hidden bg-white dark:bg-zinc-950 shadow-sm">
                                <div className="w-full p-4 overflow-x-auto">
                                    <TimetableGrid entries={groupEntries} />
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="border border-dashed border-gray-300 dark:border-gray-700 rounded-xl flex flex-col items-center justify-center bg-gray-50/50 dark:bg-zinc-900/50 py-12">
                        {generating || (loading && timetableData.length === 0) ? (
                            <div className="flex flex-col items-center gap-4">
                                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                                <p>{generating ? "AI is solving constraints... This may take a minute." : "Fetching..."}</p>
                                {taskId && <span className="text-xs text-muted-foreground text-center">Task ID: {taskId}</span>}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center gap-4 opacity-50">
                                <Calendar className="h-16 w-16" />
                                <p>No timetable generated for this term yet.</p>
                                <Button variant="link" onClick={handleGenerate}>Click to Generate</Button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
