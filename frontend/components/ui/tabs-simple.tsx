"use client"

import * as React from "react"

// Temporary simplified tabs component without Radix UI
export function Tabs({ defaultValue, children, className = "" }: any) {
  const [value, setValue] = React.useState(defaultValue)
  
  return (
    <div className={className} data-value={value}>
      {React.Children.map(children, child =>
        React.cloneElement(child, { value, onValueChange: setValue })
      )}
    </div>
  )
}

export function TabsList({ children, className = "", value, onValueChange }: any) {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground ${className}`}>
      {React.Children.map(children, child =>
        React.cloneElement(child, { value, onValueChange })
      )}
    </div>
  )
}

export function TabsTrigger({ children, value: tabValue, className = "", ...props }: any) {
  const currentValue = props.value
  const onValueChange = props.onValueChange
  const isActive = currentValue === tabValue
  
  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        isActive ? 'bg-background text-foreground shadow-sm' : ''
      } ${className}`}
      onClick={() => onValueChange(tabValue)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ children, value: tabValue, className = "", ...props }: any) {
  const currentValue = props.value
  
  if (currentValue !== tabValue) return null
  
  return (
    <div className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${className}`}>
      {children}
    </div>
  )
}