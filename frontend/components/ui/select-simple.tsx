"use client"

import * as React from "react"
import { ChevronDown } from "lucide-react"

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}

interface SelectContextValue {
  value?: string
  onValueChange?: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
  selectedLabel?: string
  setSelectedLabel: (label: string) => void
}

const SelectContext = React.createContext<SelectContextValue | null>(null)

export function Select({ value, onValueChange, children }: SelectProps) {
  const [open, setOpen] = React.useState(false)
  const [selectedLabel, setSelectedLabel] = React.useState<string>("")
  
  // Initialize selected label based on initial value
  React.useEffect(() => {
    if (value && !selectedLabel) {
      // Find the label for the initial value
      const findLabel = (elements: React.ReactNode): void => {
        React.Children.forEach(elements, (child) => {
          if (!React.isValidElement(child)) return
          
          // Check if it's SelectContent by props
          if (child.props && child.props.children) {
            // If it has SelectItem children, it's likely SelectContent
            const firstChild = React.Children.toArray(child.props.children)[0]
            if (React.isValidElement(firstChild) && firstChild.props && 'value' in firstChild.props) {
              findLabel(child.props.children)
            }
          }
          
          // Check if it's SelectItem by value prop
          if (child.props && child.props.value === value) {
            setSelectedLabel(child.props.children)
          }
        })
      }
      findLabel(children)
    }
  }, [value, children, selectedLabel])
  
  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen, selectedLabel, setSelectedLabel }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  )
}

export function SelectTrigger({ children, className = "" }: any) {
  const context = React.useContext(SelectContext)
  if (!context) return null
  
  return (
    <button
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      onClick={() => context.setOpen(!context.open)}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  )
}

export function SelectValue({ placeholder = "" }: { placeholder?: string }) {
  const context = React.useContext(SelectContext)
  if (!context) return null
  
  return <span>{context.selectedLabel || placeholder}</span>
}

export function SelectContent({ children }: any) {
  const context = React.useContext(SelectContext)
  
  // Set initial selected label based on value
  React.useEffect(() => {
    if (context && context.value) {
      React.Children.forEach(children, (child) => {
        if (React.isValidElement(child) && child.props.value === context.value) {
          context.setSelectedLabel(child.props.children)
        }
      })
    }
  }, [context?.value, children, context])
  
  if (!context || !context.open) return null
  
  return (
    <>
      <div className="fixed inset-0 z-50" onClick={() => context.setOpen(false)} />
      <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover text-popover-foreground shadow-md">
        <div className="p-1">
          {children}
        </div>
      </div>
    </>
  )
}

export function SelectItem({ children, value }: any) {
  const context = React.useContext(SelectContext)
  if (!context) return null
  
  const isSelected = context.value === value
  
  return (
    <div
      className={`relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground ${
        isSelected ? 'bg-accent text-accent-foreground' : ''
      }`}
      onClick={() => {
        context.onValueChange?.(value)
        context.setSelectedLabel(children)
        context.setOpen(false)
      }}
    >
      {isSelected && (
        <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
          <svg className="h-4 w-4" viewBox="0 0 16 16">
            <path
              fill="currentColor"
              d="M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z"
            />
          </svg>
        </span>
      )}
      {children}
    </div>
  )
}