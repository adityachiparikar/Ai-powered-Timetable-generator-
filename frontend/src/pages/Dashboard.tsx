import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
    Users,
    BookOpen,
    School,
    Calendar,
    ArrowRight,
    Activity,
    CheckCircle2,
    AlertCircle,
    BrainCircuit,
    Layers
} from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { teachersApi, coursesApi, roomsApi } from "@/services/api";

const container = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
};

export default function Dashboard() {
    const [stats, setStats] = useState({
        teachers: 0,
        courses: 0,
        rooms: 0,
        schedules: 0 // In real app, this would come from an API
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [tRes, cRes, rRes] = await Promise.all([
                    teachersApi.getAll(),
                    coursesApi.getAll(),
                    roomsApi.getAll()
                ]);
                setStats({
                    teachers: tRes.data.length,
                    courses: cRes.data.length,
                    rooms: rRes.data.length,
                    schedules: 0 // Mock for now as we don't have an endpoint for this yet
                });
            } catch (error) {
                console.error("Failed to fetch dashboard stats", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                        Dashboard
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Overview of your timetable generation system.
                    </p>
                </div>
                <Link to="/timetables">
                    <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg hover:shadow-primary/20 transition-all">
                        Generate New Timetable
                    </Button>
                </Link>
            </div>

            {/* Stats Grid */}
            <motion.div
                variants={container}
                initial="hidden"
                animate={loading ? "hidden" : "show"}
                className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
            >
                <Link to="/data-entry?tab=teachers" className="block">
                    <StatsCard
                        title="Total Teachers"
                        value={loading ? "..." : stats.teachers}
                        icon={Users}
                        trend="Active faculty members"
                        isLoading={loading}
                    />
                </Link>
                <Link to="/data-entry?tab=courses" className="block">
                    <StatsCard
                        title="Active Courses"
                        value={loading ? "..." : stats.courses}
                        icon={BookOpen}
                        trend="Across all departments"
                        isLoading={loading}
                    />
                </Link>
                <Link to="/data-entry?tab=rooms" className="block">
                    <StatsCard
                        title="Rooms Available"
                        value={loading ? "..." : stats.rooms}
                        icon={School}
                        trend="Classrooms & Labs"
                        isLoading={loading}
                    />
                </Link>
                <Link to="/timetables" className="block">
                    <StatsCard
                        title="Schedules Generated"
                        value={loading ? "..." : stats.schedules}
                        icon={Calendar}
                        trend="Total successful runs"
                        isLoading={loading}
                    />
                </Link>
            </motion.div>

            <div className="grid gap-8 md:grid-cols-2">
                {/* Quick Actions */}
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>Quick Actions</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <ActionButton
                            title="Manage Teachers"
                            desc="Add or edit faculty details"
                            href="/data-entry?tab=teachers"
                            icon={Users}
                            color="text-blue-500"
                            bg="bg-blue-500/10"
                        />
                        <ActionButton
                            title="Manage Courses"
                            desc="Define curriculum and subjects"
                            href="/data-entry?tab=courses"
                            icon={BookOpen}
                            color="text-emerald-500"
                            bg="bg-emerald-500/10"
                        />
                        <ActionButton
                            title="Manage Rooms"
                            desc="Update classroom availability"
                            href="/data-entry?tab=rooms"
                            icon={School}
                            color="text-orange-500"
                            bg="bg-orange-500/10"
                        />
                        <ActionButton
                            title="Student Batches"
                            desc="Configure student groups"
                            href="/data-entry?tab=student-groups"
                            icon={Layers}
                            color="text-pink-500"
                            bg="bg-pink-500/10"
                        />
                        <ActionButton
                            title="Configure AI Constraints"
                            desc="Adjust soft constraints for the solver"
                            href="/constraints"
                            icon={Activity}
                            color="text-purple-500"
                            bg="bg-purple-500/10"
                        />
                    </CardContent>
                </Card>

                {/* System Status */}
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>System Health</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between p-4 rounded-lg bg-green-500/5 border border-green-500/10">
                            <div className="flex items-center gap-4">
                                <div className="p-2 rounded-full bg-green-500/20 text-green-600">
                                    <CheckCircle2 className="w-5 h-5" />
                                </div>
                                <div>
                                    <p className="font-medium">Solver Engine</p>
                                    <p className="text-sm text-muted-foreground">Operational</p>
                                </div>
                            </div>
                            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                            <div className="flex items-center gap-4">
                                <div className="p-2 rounded-full bg-indigo-500/20 text-indigo-600">
                                    <BrainCircuit className="w-5 h-5" />
                                </div>
                                <div>
                                    <p className="font-medium">AI Assistant</p>
                                    <p className="text-sm text-muted-foreground">Connected to Ollama</p>
                                </div>
                            </div>
                            <div className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-orange-500/5 border border-orange-500/10">
                            <div className="flex items-center gap-4">
                                <div className="p-2 rounded-full bg-orange-500/20 text-orange-600">
                                    <AlertCircle className="w-5 h-5" />
                                </div>
                                <div>
                                    <p className="font-medium">Data Validation</p>
                                    <p className="text-sm text-muted-foreground">Ready for check</p>
                                </div>
                            </div>
                            <Link to="/data-entry">
                                <Button variant="ghost" size="sm" className="text-orange-600 hover:text-orange-700 hover:bg-orange-500/10">Review</Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

function StatsCard({ title, value, icon: Icon, trend, isLoading }: any) {
    return (
        <motion.div variants={item}>
            <Card className="glass-card hover:-translate-y-1 transition-transform">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                        {title}
                    </CardTitle>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="h-8 w-16 bg-muted animate-pulse rounded" />
                    ) : (
                        <div className="text-2xl font-bold">{value}</div>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                        {trend}
                    </p>
                </CardContent>
            </Card>
        </motion.div>
    );
}

function ActionButton({ title, desc, href, icon: Icon, color, bg }: any) {
    return (
        <Link to={href} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/50 transition-colors group">
            <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${bg} ${color}`}>
                    <Icon className="w-6 h-6" />
                </div>
                <div>
                    <h3 className="font-medium group-hover:text-primary transition-colors">{title}</h3>
                    <p className="text-sm text-muted-foreground">{desc}</p>
                </div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
        </Link>
    );
}
