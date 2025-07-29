"use client"

import * as React from "react"

interface TabsProps {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
  value?: string
  onValueChange?: (value: string) => void
}

interface TabsTriggerProps {
  children: React.ReactNode
  value: string
  className?: string
}

interface TabsContentProps {
  children: React.ReactNode
  value: string
  className?: string
}

interface TabsInternalProps {
  currentValue?: string
  onValueChange?: (value: string) => void
}

// Temporary simplified tabs component without Radix UI
export function Tabs({ defaultValue, value: controlledValue, onValueChange, children, className = "" }: TabsProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue || 'insights')
  
  // Use controlled value if provided, otherwise use internal state
  const value = controlledValue !== undefined ? controlledValue : internalValue
  const setValue = onValueChange || setInternalValue
  
  return (
    <div className={className} data-value={value}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<TabsInternalProps>, { 
            currentValue: value, 
            onValueChange: setValue 
          })
        }
        return child
      })}
    </div>
  )
}

export function TabsList({ children, className = "", value, onValueChange }: TabsListProps) {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground ${className}`}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<TabsInternalProps>, { 
            currentValue: value, 
            onValueChange 
          })
        }
        return child
      })}
    </div>
  )
}

export function TabsTrigger({ children, value: tabValue, className = "", currentValue, onValueChange }: TabsTriggerProps & TabsInternalProps) {
  const isActive = currentValue === tabValue
  
  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        isActive ? 'bg-background text-foreground shadow-sm' : ''
      } ${className}`}
      onClick={() => onValueChange?.(tabValue)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ children, value: tabValue, className = "", currentValue }: TabsContentProps & TabsInternalProps) {
  
  if (currentValue !== tabValue) return null
  
  return (
    <div className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${className}`}>
      {children}
    </div>
  )
}