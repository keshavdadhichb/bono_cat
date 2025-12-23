'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { CategorySelector } from '@/components/CategorySelector'
import { ImageUploader } from '@/components/ImageUploader'
import { BrandingForm } from '@/components/BrandingForm'
import { ProcessingStatus } from '@/components/ProcessingStatus'
import { CategoryId } from '@/lib/config'
import { CatalogFormData, GarmentImage, BrandingConfig, ProcessingStatus as ProcessingStatusType } from '@/lib/types'

const STEPS = [
    { id: 1, title: 'Category', description: 'Select target audience' },
    { id: 2, title: 'Images', description: 'Upload garment photos' },
    { id: 3, title: 'Branding', description: 'Customize your catalog' },
    { id: 4, title: 'Generate', description: 'Create your catalog' },
]

const initialBranding: BrandingConfig = {
    brandName: '',
    tagline: '',
    collectionTitle: '',
    additionalText: '',
    logo: null,
    logoPreview: null,
}

export default function CreatePage() {
    const [currentStep, setCurrentStep] = useState(1)
    const [category, setCategory] = useState<CategoryId | null>(null)
    const [images, setImages] = useState<GarmentImage[]>([])
    const [branding, setBranding] = useState<BrandingConfig>(initialBranding)
    const [isProcessing, setIsProcessing] = useState(false)
    const [processingStatus, setProcessingStatus] = useState<ProcessingStatusType>({
        stage: 'uploading',
        progress: 0,
        message: 'Preparing...',
    })
    const [pdfUrl, setPdfUrl] = useState<string | null>(null)
    const [savingToDrive, setSavingToDrive] = useState(false)

    const canProceed = useCallback(() => {
        switch (currentStep) {
            case 1:
                return category !== null
            case 2:
                return images.length > 0
            case 3:
                return branding.brandName.length > 0
            default:
                return true
        }
    }, [currentStep, category, images, branding])

    const handleNext = () => {
        if (currentStep < 4) {
            setCurrentStep(currentStep + 1)
        } else if (currentStep === 4 && !isProcessing) {
            startProcessing()
        }
    }

    const handleBack = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1)
        }
    }

    const startProcessing = async () => {
        setIsProcessing(true)

        try {
            // Stage 1: Upload images
            setProcessingStatus({
                stage: 'uploading',
                progress: 10,
                message: 'Uploading garment images...',
            })

            const formData = new FormData()
            images.forEach((img, i) => {
                formData.append(`image_${i}`, img.file)
                formData.append(`type_${i}`, img.type)
            })
            if (branding.logo) {
                formData.append('logo', branding.logo)
            }
            formData.append('category', category || 'teen_boy')
            formData.append('brandName', branding.brandName)
            formData.append('tagline', branding.tagline)
            formData.append('collectionTitle', branding.collectionTitle)
            formData.append('additionalText', branding.additionalText)

            // Upload to API
            const uploadRes = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            })

            if (!uploadRes.ok) {
                throw new Error('Failed to upload images')
            }

            const { jobId } = await uploadRes.json()

            // Stage 2: Generate AI models
            setProcessingStatus({
                stage: 'generating',
                progress: 30,
                message: 'Generating AI models with your garments...',
                currentItem: 1,
                totalItems: images.length,
            })

            // Poll for generation status
            let attempts = 0
            const maxAttempts = 60 // 5 minutes max

            while (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 5000))

                const statusRes = await fetch(`/api/status/${jobId}`)
                const status = await statusRes.json()

                if (status.stage === 'complete') {
                    // Stage 3: Assemble catalog
                    setProcessingStatus({
                        stage: 'assembling',
                        progress: 80,
                        message: 'Creating your PDF catalog...',
                    })

                    // Get PDF
                    const catalogRes = await fetch('/api/catalog', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ jobId }),
                    })

                    if (!catalogRes.ok) {
                        throw new Error('Failed to generate catalog')
                    }

                    const { pdfUrl: url } = await catalogRes.json()
                    setPdfUrl(url)

                    setProcessingStatus({
                        stage: 'complete',
                        progress: 100,
                        message: 'Your catalog is ready!',
                    })
                    break
                } else if (status.stage === 'error') {
                    throw new Error(status.error || 'Generation failed')
                } else {
                    setProcessingStatus({
                        stage: 'generating',
                        progress: 30 + (status.progress || 0) * 0.5,
                        message: status.message || 'Generating AI models...',
                        currentItem: status.currentItem,
                        totalItems: status.totalItems,
                    })
                }

                attempts++
            }

            if (attempts >= maxAttempts) {
                throw new Error('Generation timed out')
            }

        } catch (error) {
            setProcessingStatus({
                stage: 'error',
                progress: 0,
                message: error instanceof Error ? error.message : 'An error occurred',
            })
        }
    }

    const handleDownload = () => {
        if (pdfUrl) {
            window.open(pdfUrl, '_blank')
        }
    }

    const handleSaveToDrive = async () => {
        if (!pdfUrl) return

        setSavingToDrive(true)
        try {
            const res = await fetch('/api/drive/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pdfUrl }),
            })

            if (res.ok) {
                alert('Saved to Google Drive!')
            }
        } catch (error) {
            alert('Failed to save to Drive')
        } finally {
            setSavingToDrive(false)
        }
    }

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="border-b border-white/5 bg-gray-950/80 backdrop-blur-xl">
                <div className="max-w-5xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                            <span>Back</span>
                        </Link>
                        <h1 className="font-semibold">Create Catalog</h1>
                        <div className="w-16" /> {/* Spacer */}
                    </div>
                </div>
            </header>

            {/* Progress Steps */}
            <div className="border-b border-white/5">
                <div className="max-w-3xl mx-auto px-6 py-6">
                    <div className="flex items-center justify-between">
                        {STEPS.map((step, index) => (
                            <div key={step.id} className="flex items-center">
                                <div className="flex flex-col items-center">
                                    <div className={`
                    w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm
                    ${currentStep > step.id
                                            ? 'bg-emerald-500 text-white'
                                            : currentStep === step.id
                                                ? 'bg-violet-500 text-white'
                                                : 'bg-gray-800 text-gray-500'
                                        }
                  `}>
                                        {currentStep > step.id ? <Check className="w-5 h-5" /> : step.id}
                                    </div>
                                    <div className="mt-2 text-center hidden sm:block">
                                        <p className={`text-sm font-medium ${currentStep >= step.id ? 'text-white' : 'text-gray-500'}`}>
                                            {step.title}
                                        </p>
                                        <p className="text-xs text-gray-500">{step.description}</p>
                                    </div>
                                </div>
                                {index < STEPS.length - 1 && (
                                    <div className={`
                    h-0.5 w-12 sm:w-24 mx-2
                    ${currentStep > step.id ? 'bg-emerald-500' : 'bg-gray-800'}
                  `} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-12">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        {/* Step 1: Category */}
                        {currentStep === 1 && (
                            <div className="space-y-6">
                                <div className="text-center">
                                    <h2 className="text-2xl font-bold mb-2">Select Category</h2>
                                    <p className="text-gray-400">Choose the target audience for your catalog</p>
                                </div>
                                <CategorySelector selected={category} onSelect={setCategory} />
                            </div>
                        )}

                        {/* Step 2: Images */}
                        {currentStep === 2 && (
                            <div className="space-y-6">
                                <div className="text-center">
                                    <h2 className="text-2xl font-bold mb-2">Upload Garment Images</h2>
                                    <p className="text-gray-400">Add flat-lay photos of your t-shirts (front and back)</p>
                                </div>
                                <ImageUploader images={images} onImagesChange={setImages} />
                            </div>
                        )}

                        {/* Step 3: Branding */}
                        {currentStep === 3 && (
                            <div className="space-y-6">
                                <div className="text-center">
                                    <h2 className="text-2xl font-bold mb-2">Brand Your Catalog</h2>
                                    <p className="text-gray-400">Add your logo and customize the catalog text</p>
                                </div>
                                <BrandingForm branding={branding} onBrandingChange={setBranding} />
                            </div>
                        )}

                        {/* Step 4: Generate */}
                        {currentStep === 4 && (
                            <div className="space-y-6">
                                {!isProcessing ? (
                                    <div className="text-center">
                                        <h2 className="text-2xl font-bold mb-2">Ready to Generate</h2>
                                        <p className="text-gray-400 mb-8">Review your settings and click generate to create your catalog</p>

                                        <Card variant="glass" className="p-6 max-w-md mx-auto text-left space-y-4">
                                            <div className="flex justify-between">
                                                <span className="text-gray-400">Category</span>
                                                <span className="font-medium">Teen Boy</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-400">Images</span>
                                                <span className="font-medium">{images.length} garments</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-400">Brand</span>
                                                <span className="font-medium">{branding.brandName || 'Not set'}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-400">Collection</span>
                                                <span className="font-medium">{branding.collectionTitle || 'Not set'}</span>
                                            </div>
                                        </Card>
                                    </div>
                                ) : (
                                    <ProcessingStatus
                                        status={processingStatus}
                                        pdfUrl={pdfUrl || undefined}
                                        onDownload={handleDownload}
                                        onSaveToDrive={handleSaveToDrive}
                                        savingToDrive={savingToDrive}
                                    />
                                )}
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </main>

            {/* Footer Navigation */}
            {!(isProcessing && currentStep === 4) && (
                <div className="fixed bottom-0 left-0 right-0 bg-gray-950/80 backdrop-blur-xl border-t border-white/5">
                    <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between">
                        <Button
                            variant="ghost"
                            onClick={handleBack}
                            disabled={currentStep === 1}
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>

                        <Button
                            onClick={handleNext}
                            disabled={!canProceed()}
                        >
                            {currentStep === 4 ? 'Generate Catalog' : 'Continue'}
                            {currentStep < 4 && <ArrowRight className="w-4 h-4 ml-2" />}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
