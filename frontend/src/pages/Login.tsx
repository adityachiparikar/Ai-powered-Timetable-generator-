import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import api from "@/services/api";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await api.post("/login/access-token", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const { access_token } = response.data;
            localStorage.setItem("token", access_token);
            navigate("/");
        } catch (err: any) {
            console.error(err);
            setError("Invalid credentials. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-background relative overflow-hidden px-4">
            <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/30 via-background to-background -z-10" />

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative"
            >
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 flex items-center justify-center">
                    <div className="p-3 bg-primary/20 backdrop-blur-md rounded-full shadow-xl mb-4">
                        <Sparkles className="w-8 h-8 text-primary" />
                    </div>
                </div>

                <Card className="glass-card border-t-white/50">
                    <CardHeader className="space-y-1 text-center pt-10">
                        <CardTitle className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                            Timetable AI
                        </CardTitle>
                        <CardDescription>
                            Sign in to access your dashboard
                        </CardDescription>
                    </CardHeader>
                    <form onSubmit={handleLogin}>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="username">Username / Email</Label>
                                <Input
                                    id="username"
                                    type="text"
                                    placeholder="admin@university.edu"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="bg-white/5 border-white/10 focus:border-primary/50 transition-colors"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="bg-white/5 border-white/10 focus:border-primary/50 transition-colors"
                                />
                            </div>
                            {error && <p className="text-sm text-red-500 font-medium text-center bg-red-500/10 p-2 rounded">{error}</p>}
                        </CardContent>
                        <CardFooter>
                            <Button className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg shadow-primary/20 transition-all duration-300 transform hover:-translate-y-0.5" type="submit" disabled={loading}>
                                {loading ? "Signing in..." : "Sign In"}
                            </Button>
                        </CardFooter>
                    </form>
                </Card>
                <p className="mt-8 text-center text-sm text-muted-foreground">
                    &copy; {new Date().getFullYear()} AI Timetable Generator
                </p>
            </motion.div>
        </div>
    );
}
