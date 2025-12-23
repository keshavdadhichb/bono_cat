'use client'

import { useCallback, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, ImageIcon } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { GarmentImage } from '@/lib/types'
import { formatFileSize } from '@/lib/utils'

interface ImageUploaderProps {
    images: GarmentImage[]
    onImagesChange: (images: GarmentImage[]) => void
    maxImages?: number
}

export function ImageUploader({ images, onImagesChange, maxImages = 10 }: ImageUploaderProps) {
    const [isDragging, setIsDragging] = useState(false)

    const handleFiles = useCallback((files: FileList | null) => {
        if (!files) return

        const newImages: GarmentImage[] = []
        const remainingSlots = maxImages - images.length

        Array.from(files).slice(0, remainingSlots).forEach((file) => {
            if (file.type.startsWith('image/')) {
                const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
                newImages.push({
                    id,
                    file,
                    preview: URL.createObjectURL(file),
                    name: file.name,
                    type: 'front',
                })
            }
        })

        onImagesChange([...images, ...newImages])
    }, [images, maxImages, onImagesChange])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
    }, [handleFiles])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    const removeImage = useCallback((id: string) => {
        const image = images.find(img => img.id === id)
        if (image) {
            URL.revokeObjectURL(image.preview)
        }
        onImagesChange(images.filter(img => img.id !== id))
    }, [images, onImagesChange])

    const toggleImageType = useCallback((id: string) => {
        onImagesChange(images.map(img =>
            img.id === id
                ? { ...img, type: img.type === 'front' ? 'back' : 'front' }
                : img
        ))
    }, [images, onImagesChange])

    return (
        <div className="space-y-6">
            {/* Drop Zone */}
            <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`
          border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300
          ${isDragging
                        ? 'border-violet-500 bg-violet-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }
        `}
            >
                <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={(e) => handleFiles(e.target.files)}
                    className="hidden"
                    id="image-upload"
                />
                <label htmlFor="image-upload" className="cursor-pointer">
                    <div className="flex flex-col items-center gap-4">
                        <div className={`
              p-4 rounded-full transition-all duration-300
              ${isDragging ? 'bg-violet-500/20' : 'bg-gray-800'}
            `}>
                            <Upload className={`w-8 h-8 ${isDragging ? 'text-violet-400' : 'text-gray-400'}`} />
                        </div>
                        <div>
                            <p className="text-white font-medium">
                                Drop your garment images here
                            </p>
                            <p className="text-sm text-gray-400 mt-1">
                                or click to browse • PNG, JPG up to 10MB
                            </p>
                        </div>
                    </div>
                </label>
            </div>

            {/* Image Grid */}
            {images.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    <AnimatePresence>
                        {images.map((image) => (
                            <motion.div
                                key={image.id}
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                            >
                                <Card variant="glass" className="p-2 relative group">
                                    {/* Remove Button */}
                                    <button
                                        onClick={() => removeImage(image.id)}
                                        className="absolute -top-2 -right-2 z-10 p-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <X className="w-4 h-4 text-white" />
                                    </button>

                                    {/* Image Preview */}
                                    <div className="aspect-square rounded-lg overflow-hidden bg-gray-800 mb-2">
                                        <img
                                            src={image.preview}
                                            alt={image.name}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>

                                    {/* Image Info */}
                                    <div className="space-y-2">
                                        <p className="text-xs text-gray-400 truncate">{image.name}</p>

                                        {/* Type Toggle */}
                                        <button
                                            onClick={() => toggleImageType(image.id)}
                                            className={`
                        w-full py-1 px-2 rounded-lg text-xs font-medium transition-colors
                        ${image.type === 'front'
                                                    ? 'bg-violet-500/20 text-violet-400'
                                                    : 'bg-emerald-500/20 text-emerald-400'
                                                }
                      `}
                                        >
                                            {image.type === 'front' ? '👕 Front' : '👔 Back'}
                                        </button>
                                    </div>
                                </Card>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Status */}
            <p className="text-sm text-gray-500 text-center">
                {images.length} of {maxImages} images uploaded
            </p>
        </div>
    )
}
