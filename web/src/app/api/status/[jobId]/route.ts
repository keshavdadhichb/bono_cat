import { NextRequest, NextResponse } from 'next/server'
import { readFile, access } from 'fs/promises'
import { join } from 'path'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ jobId: string }> }
) {
    try {
        const { jobId } = await params
        const jobDir = join(process.cwd(), '..', 'temp', jobId)
        const metadataPath = join(jobDir, 'metadata.json')

        // Check if job exists
        try {
            await access(metadataPath)
        } catch {
            return NextResponse.json(
                { error: 'Job not found' },
                { status: 404 }
            )
        }

        const metadataContent = await readFile(metadataPath, 'utf-8')
        const metadata = JSON.parse(metadataContent)

        // Return status based on what's in metadata
        const status = metadata.generationStatus || {
            stage: metadata.status === 'complete' ? 'complete' : 'generating',
            progress: metadata.progress || 50,
            message: metadata.statusMessage || 'Processing...',
            currentItem: metadata.currentItem,
            totalItems: metadata.images?.length,
            error: metadata.error,
        }

        return NextResponse.json(status)

    } catch (error) {
        console.error('Status check error:', error)
        return NextResponse.json(
            { error: 'Failed to check status' },
            { status: 500 }
        )
    }
}
