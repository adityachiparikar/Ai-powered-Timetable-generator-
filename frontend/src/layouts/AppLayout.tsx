import { Link, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, Calendar, Settings, BrainCircuit, Database, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: Calendar, label: "Timetables", href: "/timetables" },
    { icon: Database, label: "Master Data", href: "/data-entry" },
    { icon: BrainCircuit, label: "AI Constraints", href: "/constraints" },
    { icon: Settings, label: "Settings", href: "/settings" },
];

export function AppLayout() {
    const location = useLocation();

    return (
        <div className="flex h-screen bg-background relative overflow-hidden">
            {/* Background Decor */}
            <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background -z-10" />

            {/* Sidebar */}
            <aside className="w-72 border-r border-border/50 bg-background/60 backdrop-blur-xl flex flex-col z-20 shadow-xl">
                <Link to="/" className="p-8 flex items-center gap-3 hover:opacity-80 transition-opacity">
                    <div className="p-2 bg-primary/10 rounded-xl">
                        <Sparkles className="w-6 h-6 text-primary" />
                    </div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                        Timetable AI
                    </h1>
                </Link>

                <nav className="flex-1 px-4 space-y-2 overflow-y-auto py-4">
                    {sidebarItems.map((item) => {
                        const isActive = location.pathname === item.href || (item.href !== "/" && location.pathname.startsWith(item.href));
                        return (
                            <Link
                                key={item.label}
                                to={item.href}
                                className={cn(
                                    "relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 group overflow-hidden",
                                    isActive
                                        ? "text-primary bg-primary/10 shadow-sm"
                                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                                )}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="sidebar-active"
                                        className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full"
                                    />
                                )}
                                <item.icon className={cn("w-5 h-5 transition-transform group-hover:scale-110", isActive && "fill-current opacity-100")} />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 m-4 rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 text-white shadow-lg relative overflow-hidden group">
                    <div className="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative px-4 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white font-bold border border-white/20">
                                AD
                            </div>
                            <div>
                                <p className="text-sm font-semibold">Admin User</p>
                                <p className="text-xs text-gray-400">admin@university.edu</p>
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                localStorage.removeItem("token");
                                window.location.href = "/login";
                            }}
                            className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                            title="Logout"
                        >
                            <Settings className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto overflow-x-hidden relative">
                <div className="p-8 max-w-7xl mx-auto min-h-full">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
