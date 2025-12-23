'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'glass' | 'gradient'
    interactive?: boolean
    selected?: boolean
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = 'default', interactive, selected, children, ...props }, ref) => {
        const variants = {
            default: 'bg-gray-900/50 border border-gray-800',
            glass: 'bg-white/5 backdrop-blur-xl border border-white/10',
            gradient: 'bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700',
        }

        return (
            <div
                ref={ref}
                className={cn(
                    'rounded-2xl p-6',
                    variants[variant],
                    interactive && 'cursor-pointer transition-all duration-300 hover:border-violet-500/50 hover:shadow-lg hover:shadow-violet-500/10',
                    selected && 'border-violet-500 ring-2 ring-violet-500/30 shadow-lg shadow-violet-500/20',
                    className
                )}
                {...props}
            >
                {children}
            </div>
        )
    }
)
Card.displayName = 'Card'

export { Card }
