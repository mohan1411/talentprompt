"use client"

import * as React from "react"

interface SliderProps {
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
  className?: string
}

export function Slider({ 
  value = [0], 
  onValueChange, 
  min = 0, 
  max = 100, 
  step = 1,
  className = ""
}: SliderProps) {
  const percentage = ((value[0] - min) / (max - min)) * 100

  return (
    <div className={`relative flex w-full touch-none select-none items-center ${className}`}>
      <div className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
        <div 
          className="absolute h-full bg-primary" 
          style={{ width: `${percentage}%` }}
        />
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onValueChange([Number(e.target.value)])}
        className="absolute inset-0 w-full opacity-0 cursor-pointer"
      />
      <div 
        className="absolute block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
        style={{ left: `calc(${percentage}% - 10px)` }}
      />
    </div>
  )
}