'use client'

import { motion } from 'framer-motion'
import { Loader2, CheckCircle, AlertCircle, Download, Cloud } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ProcessingStatus as ProcessingStatusType } from '@/lib/types'

interface ProcessingStatusProps {
    status: ProcessingStatusType
    pdfUrl?: string
    onDownload?: () => void
    onSaveToDrive?: () => void
    savingToDrive?: boolean
}

export function ProcessingStatus({
    status,
    pdfUrl,
    onDownload,
    onSaveToDrive,
    savingToDrive
}: ProcessingStatusProps) {
    const stages = [
        { id: 'uploading', label: 'Uploading Images', icon: '📤' },
        { id: 'generating', label: 'Generating AI Models', icon: '🤖' },
        { id: 'assembling', label: 'Creating Catalog', icon: '📄' },
        { id: 'complete', label: 'Complete!', icon: '✅' },
    ]

    const currentStageIndex = stages.findIndex(s => s.id === status.stage)

    if (status.stage === 'error') {
        return (
            <Card variant="glass" className="p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Something went wrong</h3>
                <p className="text-gray-400">{status.message}</p>
            </Card>
        )
    }

    if (status.stage === 'complete') {
        return (
            <Card variant="gradient" className="p-8 text-center">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', bounce: 0.5 }}
                    className="w-20 h-20 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center mx-auto mb-6"
                >
                    <CheckCircle className="w-10 h-10 text-white" />
                </motion.div>

                <h3 className="text-2xl font-bold text-white mb-2">Catalog Ready!</h3>
                <p className="text-gray-400 mb-8">Your fashion catalog has been generated successfully.</p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button size="lg" onClick={onDownload}>
                        <Download className="w-5 h-5 mr-2" />
                        Download PDF
                    </Button>
                    <Button
                        size="lg"
                        variant="secondary"
                        onClick={onSaveToDrive}
                        loading={savingToDrive}
                    >
                        <Cloud className="w-5 h-5 mr-2" />
                        Save to Google Drive
                    </Button>
                </div>
            </Card>
        )
    }

    return (
        <Card variant="glass" className="p-8">
            {/* Progress Steps */}
            <div className="flex items-center justify-between mb-8">
                {stages.slice(0, -1).map((stage, index) => {
                    const isComplete = index < currentStageIndex
                    const isCurrent = index === currentStageIndex

                    return (
                        <div key={stage.id} className="flex items-center">
                            <div className={`
                w-10 h-10 rounded-full flex items-center justify-center text-lg
                ${isComplete ? 'bg-emerald-500' : isCurrent ? 'bg-violet-500' : 'bg-gray-700'}
              `}>
                                {isComplete ? '✓' : stage.icon}
                            </div>
                            {index < stages.length - 2 && (
                                <div className={`
                  h-1 w-16 mx-2
                  ${index < currentStageIndex ? 'bg-emerald-500' : 'bg-gray-700'}
                `} />
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Current Stage */}
            <div className="text-center">
                <div className="flex items-center justify-center gap-3 mb-4">
                    <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
                    <h3 className="text-xl font-semibold text-white">
                        {stages[currentStageIndex]?.label}
                    </h3>
                </div>

                <p className="text-gray-400 mb-6">{status.message}</p>

                {/* Progress Bar */}
                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-violet-500 to-indigo-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${status.progress}%` }}
                        transition={{ duration: 0.5 }}
                    />
                </div>

                <p className="text-sm text-gray-500 mt-2">
                    {status.currentItem && status.totalItems
                        ? `Processing ${status.currentItem} of ${status.totalItems} items`
                        : `${status.progress}% complete`
                    }
                </p>
            </div>
        </Card>
    )
}
