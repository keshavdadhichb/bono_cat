// Types for the catalog creation flow

export interface GarmentImage {
    id: string
    file: File
    preview: string
    name: string
    type: 'front' | 'back'
}

export interface BrandingConfig {
    brandName: string
    tagline: string
    collectionTitle: string
    additionalText: string
    logo: File | null
    logoPreview: string | null
}

export interface CatalogFormData {
    category: string
    garments: GarmentImage[]
    branding: BrandingConfig
}

export interface ProcessingStatus {
    stage: 'uploading' | 'generating' | 'assembling' | 'complete' | 'error'
    progress: number
    message: string
    currentItem?: number
    totalItems?: number
}

export interface GeneratedResult {
    jobId: string
    images: {
        fullBody: string
        closeup?: string
        garmentName: string
    }[]
    pdfUrl?: string
    driveUrl?: string
}
