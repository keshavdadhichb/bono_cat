import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const { pdfUrl, jobId } = await request.json()
        const apiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000'

        // Call Python API to upload to Google Drive
        const response = await fetch(`${apiUrl}/drive/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pdfUrl, jobId }),
        })

        if (!response.ok) {
            throw new Error('Failed to upload to Drive')
        }

        const result = await response.json()

        return NextResponse.json({
            success: true,
            driveUrl: result.driveUrl,
            fileId: result.fileId,
        })

    } catch (error) {
        console.error('Drive upload error:', error)
        return NextResponse.json(
            { error: 'Failed to upload to Google Drive' },
            { status: 500 }
        )
    }
}
