'use client'

import { motion } from 'framer-motion'
import { Card } from '@/components/ui/Card'
import { CATEGORIES, type CategoryId } from '@/lib/config'
import { Lock } from 'lucide-react'

interface CategorySelectorProps {
    selected: CategoryId | null
    onSelect: (category: CategoryId) => void
}

export function CategorySelector({ selected, onSelect }: CategorySelectorProps) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {CATEGORIES.map((category, index) => (
                <motion.div
                    key={category.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                >
                    <Card
                        variant="glass"
                        interactive={category.available}
                        selected={selected === category.id}
                        onClick={() => category.available && onSelect(category.id)}
                        className={`relative ${!category.available ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {!category.available && (
                            <div className="absolute top-3 right-3">
                                <Lock className="w-4 h-4 text-gray-500" />
                            </div>
                        )}
                        <div className="text-center">
                            <div className="text-4xl mb-3">{category.icon}</div>
                            <h3 className="font-semibold text-white mb-1">{category.name}</h3>
                            <p className="text-sm text-gray-400">
                                {category.available ? category.description : 'Coming Soon'}
                            </p>
                        </div>
                    </Card>
                </motion.div>
            ))}
        </div>
    )
}
