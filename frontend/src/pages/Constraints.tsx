import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Save } from "lucide-react";

import { ConstraintChatbot } from "@/components/ConstraintChatbot";

export default function Constraints() {
    // Default State
    const [maxDailyLoad, setMaxDailyLoad] = useState(4);
    const [minimizeGaps, setMinimizeGaps] = useState(true);
    const [consecutiveLabs, setConsecutiveLabs] = useState(true);
    const [parallelLabs, setParallelLabs] = useState(true);

    const [saved, setSaved] = useState(false);

    // Load from LocalStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem("solver_config");
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (parsed.max_daily_load) setMaxDailyLoad(parsed.max_daily_load);
                if (parsed.minimize_gaps !== undefined) setMinimizeGaps(parsed.minimize_gaps);
                if (parsed.consecutive_labs !== undefined) setConsecutiveLabs(parsed.consecutive_labs);
                if (parsed.parallel_labs !== undefined) setParallelLabs(parsed.parallel_labs);
            } catch (e) {
                console.error("Failed to parse config", e);
            }
        }
    }, []);

    const handleSave = (overrides?: any) => {
        const config = {
            max_daily_load: overrides?.max_daily_load ?? maxDailyLoad,
            minimize_gaps: overrides?.minimize_gaps ?? minimizeGaps,
            consecutive_labs: overrides?.consecutive_labs ?? consecutiveLabs,
            parallel_labs: overrides?.parallel_labs ?? parallelLabs
        };
        localStorage.setItem("solver_config", JSON.stringify(config));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleChatUpdate = (updates: any) => {
        let hasChanges = false;
        if (updates.max_daily_load !== undefined) { setMaxDailyLoad(updates.max_daily_load); hasChanges = true; }
        if (updates.minimize_gaps !== undefined) { setMinimizeGaps(updates.minimize_gaps); hasChanges = true; }
        if (updates.consecutive_labs !== undefined) { setConsecutiveLabs(updates.consecutive_labs); hasChanges = true; }
        if (updates.parallel_labs !== undefined) { setParallelLabs(updates.parallel_labs); hasChanges = true; }

        if (hasChanges) {
            // Auto-save chat changes to localStorage
            handleSave(updates);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">AI Constraints</h2>
                    <p className="text-muted-foreground">Configure the rules for the timetable generator.</p>
                </div>
                <Button onClick={handleSave} className="gap-2">
                    <Save className="w-4 h-4" />
                    {saved ? "Saved!" : "Save Changes"}
                </Button>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Soft Constraints (Preferences)</CardTitle>
                            <CardDescription>Rules that the AI will try to optimize for, but may break if necessary.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-8">

                            {/* Max Daily Load */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label htmlFor="max-load" className="text-base font-medium">Max Daily Load per Teacher</Label>
                                    <span className="text-sm font-bold bg-blue-100 text-blue-800 px-2 py-1 rounded dark:bg-blue-900 dark:text-blue-300">
                                        {maxDailyLoad} Hours
                                    </span>
                                </div>
                                <Slider
                                    id="max-load"
                                    min={2}
                                    max={8}
                                    step={1}
                                    value={[maxDailyLoad]}
                                    onValueChange={(vals) => setMaxDailyLoad(vals[0])}
                                />
                                <p className="text-sm text-gray-500">
                                    Prefer not to schedule a teacher for more than {maxDailyLoad} hours in a single day.
                                </p>
                            </div>

                            <div className="border-t pt-6"></div>

                            <div className="flex items-start space-x-4">
                                <div className="flex-1 space-y-1">
                                    <Label htmlFor="min-gaps" className="text-base font-medium">Minimize Gaps</Label>
                                    <p className="text-sm text-gray-500">
                                        Try to schedule classes consecutively to avoid free hours between lectures for teachers.
                                    </p>
                                </div>
                                <Switch
                                    id="min-gaps"
                                    checked={minimizeGaps}
                                    onCheckedChange={setMinimizeGaps}
                                />
                            </div>

                            <div className="border-t pt-6"></div>

                            {/* Consecutive Labs */}
                            <div className="flex items-start space-x-4">
                                <div className="flex-1 space-y-1">
                                    <Label htmlFor="consecutive-labs" className="text-base font-medium">Consecutive 2-Hour Labs</Label>
                                    <p className="text-sm text-gray-500">
                                        Force all laboratory sessions to be scheduled in continuous 2-hour blocks.
                                    </p>
                                </div>
                                <Switch
                                    id="consecutive-labs"
                                    checked={consecutiveLabs}
                                    onCheckedChange={setConsecutiveLabs}
                                />
                            </div>

                            <div className="border-t pt-6"></div>

                            {/* Parallel Labs */}
                            <div className="flex items-start space-x-4">
                                <div className="flex-1 space-y-1">
                                    <Label htmlFor="parallel-labs" className="text-base font-medium">Parallel Division Labs</Label>
                                    <p className="text-sm text-gray-500">
                                        Try to schedule all batches (B1, B2, B3) of a division to have labs at the same time.
                                    </p>
                                </div>
                                <Switch
                                    id="parallel-labs"
                                    checked={parallelLabs}
                                    onCheckedChange={setParallelLabs}
                                />
                            </div>

                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Hard Constraints</CardTitle>
                            <CardDescription>Rules that cannot be broken. These are always active.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <ul className="list-disc pl-4 space-y-2 text-sm text-gray-600 dark:text-gray-400">
                                <li><strong>Teacher Conflict:</strong> A teacher cannot be in two places at once.</li>
                                <li><strong>Room Conflict:</strong> A room cannot host two classes at once.</li>
                                <li><strong>Student Group Conflict:</strong> A batch/group cannot attend two classes at once.</li>
                                <li><strong>Room Capability:</strong> Labs must be held in Lab rooms.</li>
                                <li><strong>Room Capacity:</strong> Room size must accommodate the batch size.</li>
                            </ul>
                        </CardContent>
                    </Card>
                </div>

                <div className="lg:col-span-1">
                    <ConstraintChatbot
                        currentConfig={{
                            max_daily_load: maxDailyLoad,
                            minimize_gaps: minimizeGaps,
                            consecutive_labs: consecutiveLabs,
                            parallel_labs: parallelLabs,
                        }}
                        onConfigUpdate={handleChatUpdate}
                    />
                </div>
            </div>
        </div>
    );
}
