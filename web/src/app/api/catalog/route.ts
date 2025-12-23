import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const { jobId } = await request.json()
        const apiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000'

        // Call Python API to generate catalog PDF
        const response = await fetch(`${apiUrl}/catalog`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jobId }),
        })

        if (!response.ok) {
            throw new Error('Failed to generate catalog')
        }

        const result = await response.json()

        return NextResponse.json({
            success: true,
            pdfUrl: result.pdfUrl || `/api/download/${jobId}`,
        })

    } catch (error) {
        console.error('Catalog generation error:', error)
        return NextResponse.json(
            { error: 'Failed to generate catalog' },
            { status: 500 }
        )
    }
}
