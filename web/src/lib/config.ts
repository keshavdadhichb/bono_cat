// API configuration
export const API_CONFIG = {
    // Python API for PDF generation (local development)
    pythonApiUrl: process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000',

    // RunPod configuration
    runpodApiKey: process.env.RUNPOD_API_KEY || '',
    runpodEndpointId: process.env.RUNPOD_ENDPOINT_ID || '',

    // Google Drive
    driveOutputFolderId: process.env.GOOGLE_DRIVE_OUTPUT_FOLDER_ID || '1y5rIsYoWiadG_sH-8KS4EDk0VjFTIJvc',
}

// Category definitions
export const CATEGORIES = [
    {
        id: 'teen_boy',
        name: 'Teen Boy',
        description: 'Ages 13-15',
        available: true,
        icon: '👦',
    },
    {
        id: 'teen_girl',
        name: 'Teen Girl',
        description: 'Ages 13-15',
        available: false,
        icon: '👧',
    },
    {
        id: 'infant_boy',
        name: 'Infant Boy',
        description: 'Ages 0-3',
        available: false,
        icon: '👶',
    },
    {
        id: 'infant_girl',
        name: 'Infant Girl',
        description: 'Ages 0-3',
        available: false,
        icon: '👶',
    },
    {
        id: 'man',
        name: 'Man',
        description: 'Adults',
        available: false,
        icon: '👨',
    },
    {
        id: 'woman',
        name: 'Woman',
        description: 'Adults',
        available: false,
        icon: '👩',
    },
] as const

export type CategoryId = typeof CATEGORIES[number]['id']
