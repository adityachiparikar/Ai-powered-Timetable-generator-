import React from 'react';

// Types (should be in a types file)
interface TimetableEntry {
    id?: string;
    course_id: string;
    course_code: string;
    day: string;
    time: string;
    room: string;
    course_type?: string;
    batch_id?: string | number;
}

interface TimetableGridProps {
    entries: TimetableEntry[];
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const SLOTS = [
    '08:00 - 09:00', '09:00 - 10:00', '10:00 - 11:00', '11:00 - 12:00',
    '12:00 - 13:00', '13:00 - 14:00', '14:00 - 15:00', '15:00 - 16:00',
    '16:00 - 17:00', '17:00 - 18:00'
];
const BREAK_SLOTS = new Set(['13:00 - 14:00']);

export default function TimetableGrid({ entries }: TimetableGridProps) {
    const normalizeTime = (time?: string) => (time || '').replace(/\s*-\s*/, ' - ');

    const getEntries = (day: string, slot: string) => {
        return entries.filter(e => e.day === day && normalizeTime(e.time) === slot);
    };

    const getStyles = (type?: string) => {
        if (type === 'LAB') return {
            bg: "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200",
            text: "text-emerald-700 dark:text-emerald-300",
            label: "Lab"
        };
        if (type === 'TUTORIAL') return {
            bg: "bg-purple-50 dark:bg-purple-900/20 border-purple-200",
            text: "text-purple-700 dark:text-purple-300",
            label: "Tut"
        };
        return {
            bg: "bg-sky-50 dark:bg-sky-900/20 border-sky-200",
            text: "text-sky-700 dark:text-sky-300",
            label: "Lec"
        };
    };

    return (
        <div className="overflow-x-auto">
            <div className="min-w-[1000px] grid grid-cols-[100px_repeat(6,1fr)] gap-2 p-1">
                {/* Header */}
                <div className="font-bold text-center p-3 text-gray-500 text-sm uppercase tracking-wider">Time \ Day</div>
                {DAYS.map(day => (
                    <div key={day} className="font-bold text-center p-3 bg-gray-50 dark:bg-zinc-900 rounded-lg text-gray-700 dark:text-zinc-300">
                        {day.slice(0, 3)}
                    </div>
                ))}

                {/* Rows */}
                {SLOTS.map((slot) => {
                    const hasEntriesInSlot = DAYS.some(day => getEntries(day, slot).length > 0);

                    if (BREAK_SLOTS.has(slot) && !hasEntriesInSlot) {
                        return (
                            <React.Fragment key={slot}>
                                <div className="flex items-center justify-center text-xs font-medium text-gray-500 bg-gray-50/50 dark:bg-zinc-900/30 rounded-lg">
                                    {slot.split(' - ')[0]}
                                </div>
                                <div className="col-span-6 min-h-10 rounded-lg border border-dashed border-amber-200 bg-amber-50/70 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300 flex items-center justify-center text-xs font-semibold uppercase tracking-wide">
                                    Break
                                </div>
                            </React.Fragment>
                        );
                    }

                    return (
                        <React.Fragment key={slot}>
                            <div className="flex items-center justify-center text-xs font-medium text-gray-500 bg-gray-50/50 dark:bg-zinc-900/30 rounded-lg">
                                {slot.split(' - ')[0]}
                            </div>
                            {DAYS.map(day => {
                                const slotEntries = getEntries(day, slot);
                                return (
                                    <div key={`${day}-${slot}`} className="min-h-[100px] p-1 border border-dashed border-gray-100 dark:border-zinc-800/50 rounded-lg flex flex-col gap-1">
                                        {slotEntries.map((entry, idx) => {
                                            const styles = getStyles(entry.course_type);
                                            return (
                                                <div
                                                    key={idx}
                                                    className={`p-2 rounded-md border shadow-sm transition-all hover:shadow-md ${styles.bg} ${styles.text} flex flex-col gap-0.5`}
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-[10px] font-bold uppercase opacity-70">{styles.label}</span>
                                                        {entry.batch_id && (
                                                            <span className="text-[10px] bg-white/50 px-1 rounded font-mono">
                                                                {entry.batch_id.toString().slice(-2).toUpperCase()}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="text-sm font-bold truncate leading-tight">
                                                        {entry.course_code}
                                                    </div>
                                                    <div className="text-[10px] font-medium mt-1 flex items-center gap-1">
                                                        <span className="opacity-60">Room:</span> {entry.room}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                );
                            })}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
}
