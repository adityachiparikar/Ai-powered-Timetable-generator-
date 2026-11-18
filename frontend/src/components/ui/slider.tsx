import * as React from "react"
import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
    HTMLInputElement,
    Omit<React.ComponentPropsWithoutRef<"input">, "value" | "onChange"> & { value: number[]; onValueChange: (vals: number[]) => void; min: number; max: number; step: number }
>(({ className, value, onValueChange, min, max, step, ...props }, ref) => (
    <div className="relative flex w-full touch-none select-none items-center">
        <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value[0]}
            onChange={(e) => onValueChange([parseFloat(e.target.value)])}
            ref={ref}
            className={cn(
                "w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer dark:bg-zinc-700 accent-primary",
                className
            )}
            {...props}
        />
    </div>
))
Slider.displayName = "Slider"

export { Slider }
