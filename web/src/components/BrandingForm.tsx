'use client'

import { useState, useCallback } from 'react'
import { Upload, X } from 'lucide-react'
import { Input, Textarea } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { BrandingConfig } from '@/lib/types'

interface BrandingFormProps {
    branding: BrandingConfig
    onBrandingChange: (branding: BrandingConfig) => void
}

export function BrandingForm({ branding, onBrandingChange }: BrandingFormProps) {
    const handleChange = (field: keyof BrandingConfig, value: string) => {
        onBrandingChange({ ...branding, [field]: value })
    }

    const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            const preview = URL.createObjectURL(file)
            onBrandingChange({
                ...branding,
                logo: file,
                logoPreview: preview
            })
        }
    }

    const removeLogo = () => {
        if (branding.logoPreview) {
            URL.revokeObjectURL(branding.logoPreview)
        }
        onBrandingChange({
            ...branding,
            logo: null,
            logoPreview: null
        })
    }

    return (
        <div className="grid md:grid-cols-2 gap-6">
            {/* Logo Upload */}
            <Card variant="glass" className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Brand Logo</h3>

                {branding.logoPreview ? (
                    <div className="relative">
                        <div className="aspect-video rounded-lg overflow-hidden bg-white flex items-center justify-center p-4">
                            <img
                                src={branding.logoPreview}
                                alt="Logo preview"
                                className="max-h-full max-w-full object-contain"
                            />
                        </div>
                        <button
                            onClick={removeLogo}
                            className="absolute -top-2 -right-2 p-1 bg-red-500 rounded-full"
                        >
                            <X className="w-4 h-4 text-white" />
                        </button>
                    </div>
                ) : (
                    <label className="block cursor-pointer">
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleLogoChange}
                            className="hidden"
                        />
                        <div className="aspect-video rounded-lg border-2 border-dashed border-gray-700 flex flex-col items-center justify-center gap-2 hover:border-violet-500 transition-colors">
                            <Upload className="w-8 h-8 text-gray-500" />
                            <p className="text-sm text-gray-400">Upload logo</p>
                        </div>
                    </label>
                )}
            </Card>

            {/* Brand Details */}
            <div className="space-y-4">
                <Input
                    label="Brand Name"
                    placeholder="e.g., BONO"
                    value={branding.brandName}
                    onChange={(e) => handleChange('brandName', e.target.value)}
                />

                <Input
                    label="Tagline"
                    placeholder="e.g., Streetwear for the Next Generation"
                    value={branding.tagline}
                    onChange={(e) => handleChange('tagline', e.target.value)}
                />

                <Input
                    label="Collection Title"
                    placeholder="e.g., Summer Collection 2024"
                    value={branding.collectionTitle}
                    onChange={(e) => handleChange('collectionTitle', e.target.value)}
                />

                <Textarea
                    label="Additional Text (Optional)"
                    placeholder="Any extra text to include in the catalog..."
                    value={branding.additionalText}
                    onChange={(e) => handleChange('additionalText', e.target.value)}
                />
            </div>
        </div>
    )
}
