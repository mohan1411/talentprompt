"use client"

import * as React from "react"

interface TabsProps {
  defaultValue: string
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
  value?: string
  onValueChange?: (value: string) => void
}

// Temporary simplified tabs component without Radix UI
export function Tabs({ defaultValue, children, className = "" }: TabsProps) {
  const [value, setValue] = React.useState(defaultValue)
  
  return (
    <div className={className} data-value={value}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<TabsInternalProps>, { 
            value, 
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
            value, 
            onValueChange 
          })
        }
        return child
      })}
    </div>
  )
}

export function TabsTrigger({ children, value: tabValue, className = "", ...props }: TabsTriggerProps & TabsInternalProps) {
  const currentValue = props.value
  const onValueChange = props.onValueChange
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

export function TabsContent({ children, value: tabValue, className = "", ...props }: TabsContentProps & TabsInternalProps) {
  const currentValue = props.value
  
  if (currentValue !== tabValue) return null
  
  return (
    <div className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${className}`}>
      {children}
    </div>
  )
}