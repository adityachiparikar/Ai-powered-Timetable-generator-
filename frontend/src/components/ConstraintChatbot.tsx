import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { aiApi } from "@/services/api";
import { Send, Bot, Check, X, Loader2 } from "lucide-react";

interface ConstraintChatbotProps {
    currentConfig: {
        max_daily_load: number;
        minimize_gaps: boolean;
        consecutive_labs: boolean;
        parallel_labs: boolean;
    };
    onConfigUpdate: (newConfig: any) => void;
}

interface Message {
    role: "user" | "assistant";
    text: string;
}

interface TimetableMove {
    entry_id: string;
    course_code: string;
    teacher?: string | null;
    student_group: string;
    room: string;
    from_day: string;
    from_time: string;
    to_day: string;
    to_time: string;
}

const TIMETABLE_UPDATED_EVENT = "timetable-updated";

export function ConstraintChatbot({ currentConfig, onConfigUpdate }: ConstraintChatbotProps) {
    const [messages, setMessages] = useState<Message[]>([
        { role: "assistant", text: "Hello! I can help you configure the soft constraints. Gap minimization is enabled by default. Try saying 'Set max load to 5' or 'move SY A sessions from Saturday'." }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [applying, setApplying] = useState(false);
    const [pendingProposal, setPendingProposal] = useState<any | null>(null);
    const [lastProposal, setLastProposal] = useState<any | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const formatError = (error: any) => {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string") return detail;
        if (error.response?.status) return `Server returned ${error.response.status}`;
        return error.message || "Unknown error";
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const isFixFollowUp = (message: string) => (
        /\b(fix|solve|resolve|clear)\b/i.test(message)
        && /\b(them|it|conflicts?|issues?)\b/i.test(message)
    );

    const isMoveFollowUp = (message: string) => (
        /\b(instead|other\s+day|another\s+day|shift\s+it|move\s+it)\b/i.test(message)
        && /\b(it|them|other|another|instead)\b/i.test(message)
    );

    const buildRelaxedMoveMessage = (proposal: any | null) => {
        const action = proposal?.action;
        const params = action?.params || {};
        const fromDay = params.from_day;
        if (!action?.type || !fromDay) return null;

        if (action.type === "MOVE_GROUP_DAY_SESSIONS" && params.group_name) {
            return `move ${params.group_name} sessions from ${fromDay} to other days`;
        }

        if (action.type === "MOVE_TEACHER_DAY_SESSIONS" && params.teacher_name) {
            return `move classes of ${params.teacher_name} from ${fromDay} to other days`;
        }

        return null;
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setInput("");
        setMessages(prev => [...prev, { role: "user", text: userMsg }]);
        setLoading(true);

        try {
            const relaxedMessage = (isFixFollowUp(userMsg) || isMoveFollowUp(userMsg))
                ? buildRelaxedMoveMessage(lastProposal)
                : null;
            if (relaxedMessage) {
                setMessages(prev => [...prev, {
                    role: "assistant",
                    text: "I am using the previous move request and checking other available days."
                }]);
            }

            const response = await aiApi.chat(relaxedMessage || userMsg, currentConfig);
            const data = response.data; // { response: str, updated_config: dict }

            setMessages(prev => [...prev, { role: "assistant", text: data.response }]);
            setLastProposal(data.proposal || null);
            setPendingProposal(data.proposal?.moves?.length ? data.proposal : null);

            if (data.updated_config) {
                // Only pass valid updates
                const updates: any = {};
                if (data.updated_config.max_daily_load !== null && data.updated_config.max_daily_load !== undefined) {
                    updates.max_daily_load = data.updated_config.max_daily_load;
                }
                if (data.updated_config.minimize_gaps !== null && data.updated_config.minimize_gaps !== undefined) {
                    updates.minimize_gaps = data.updated_config.minimize_gaps;
                }
                if (data.updated_config.consecutive_labs !== null && data.updated_config.consecutive_labs !== undefined) {
                    updates.consecutive_labs = data.updated_config.consecutive_labs;
                }
                if (data.updated_config.parallel_labs !== null && data.updated_config.parallel_labs !== undefined) {
                    updates.parallel_labs = data.updated_config.parallel_labs;
                }

                if (Object.keys(updates).length > 0) {
                    onConfigUpdate(updates);
                    setMessages(prev => [...prev, {
                        role: "assistant",
                        text: "I saved the generator preference. Existing timetable entries will not change until you click Generate New on the Timetables page."
                    }]);
                }
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: "assistant", text: `AI assistant error: ${formatError(error)}` }]);
        } finally {
            setLoading(false);
        }
    };

    const handleApplyProposal = async () => {
        if (!pendingProposal) return;
        setApplying(true);
        try {
            const response = await aiApi.applyTimetableChange(pendingProposal);
            const appliedCount = response.data.applied?.length || 0;
            const skippedCount = response.data.skipped?.length || 0;
            const suffix = appliedCount > 0
                ? " Timetable data has been updated; open or refresh the Timetables page to see it."
                : "";
            const skippedSuffix = skippedCount > 0 ? ` ${skippedCount} move(s) could not be applied due to conflicts.` : "";
            window.dispatchEvent(new CustomEvent(TIMETABLE_UPDATED_EVENT));
            localStorage.setItem("timetable_updated_at", Date.now().toString());
            setMessages(prev => [...prev, { role: "assistant", text: `${response.data.response}${suffix}${skippedSuffix}` }]);
            setPendingProposal(null);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: "assistant", text: `Apply failed: ${formatError(error)}` }]);
        } finally {
            setApplying(false);
        }
    };

    return (
        <Card className="h-[600px] flex flex-col">
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><Bot className="w-5 h-5" /> AI Assistant</CardTitle>
                <CardDescription>Chat to configure preferences</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden">
                <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                    {messages.map((m, i) => (
                        <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] p-3 rounded-lg ${m.role === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                                }`}>
                                <p className="text-sm">{m.text}</p>
                            </div>
                        </div>
                    ))}
                    {loading && <div className="text-xs text-muted-foreground animate-pulse">Thinking...</div>}
                    {pendingProposal && (
                        <div className="rounded-md border bg-white p-3 text-sm shadow-sm dark:bg-gray-900">
                            <div className="font-medium mb-2">Proposed timetable changes</div>
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                {pendingProposal.moves.map((move: TimetableMove) => (
                                    <div key={move.entry_id} className="rounded border p-2 text-xs">
                                        <div className="font-medium">{move.course_code} - {move.student_group}</div>
                                        <div className="text-muted-foreground">
                                            {move.from_day} {move.from_time} to {move.to_day} {move.to_time}
                                        </div>
                                        <div className="text-muted-foreground">
                                            {move.teacher || "Unassigned"} / {move.room}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            {pendingProposal.conflicts?.length > 0 && (
                                <div className="mt-2 text-xs text-amber-700">
                                    {pendingProposal.conflicts.length} conflict(s) could not be moved.
                                </div>
                            )}
                            <div className="mt-3 flex gap-2">
                                <Button size="sm" onClick={handleApplyProposal} disabled={applying} className="gap-2">
                                    {applying ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                    Apply
                                </Button>
                                <Button size="sm" variant="outline" onClick={() => setPendingProposal(null)} disabled={applying} className="gap-2">
                                    <X className="w-3 h-3" />
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    )}
                    {!pendingProposal && lastProposal?.conflicts?.length > 0 && (
                        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 shadow-sm">
                            <div className="font-medium">No direct move available</div>
                            <p className="mt-1 text-xs">
                                The requested target day has conflicts. Type "fix them" to let the assistant try other days.
                            </p>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div className="flex gap-2 pt-2">
                    <Input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSend()}
                        placeholder="Type a message..."
                        disabled={loading}
                    />
                    <Button onClick={handleSend} disabled={loading || !input.trim()} size="icon">
                        <Send className="w-4 h-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
