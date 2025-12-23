import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { join } from 'path'
import { randomUUID } from 'crypto'

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData()
        const jobId = randomUUID()

        // Create job directory
        const jobDir = join(process.cwd(), '..', 'temp', jobId)
        await mkdir(jobDir, { recursive: true })
        await mkdir(join(jobDir, 'garments'), { recursive: true })

        // Extract metadata
        const category = formData.get('category') as string
        const brandName = formData.get('brandName') as string
        const tagline = formData.get('tagline') as string
        const collectionTitle = formData.get('collectionTitle') as string
        const additionalText = formData.get('additionalText') as string

        // Save metadata
        const metadata = {
            jobId,
            category,
            brandName,
            tagline,
            collectionTitle,
            additionalText,
            images: [] as { name: string; type: string; path: string }[],
            logoPath: null as string | null,
            createdAt: new Date().toISOString(),
            status: 'pending',
        }

        // Save logo if provided
        const logo = formData.get('logo') as File | null
        if (logo) {
            const logoBuffer = Buffer.from(await logo.arrayBuffer())
            const logoPath = join(jobDir, 'logo.png')
            await writeFile(logoPath, logoBuffer)
            metadata.logoPath = logoPath
        }

        // Save garment images
        let imageIndex = 0
        while (formData.has(`image_${imageIndex}`)) {
            const image = formData.get(`image_${imageIndex}`) as File
            const type = formData.get(`type_${imageIndex}`) as string

            if (image) {
                const buffer = Buffer.from(await image.arrayBuffer())
                const filename = `garment_${imageIndex}_${type}.png`
                const imagePath = join(jobDir, 'garments', filename)
                await writeFile(imagePath, buffer)

                metadata.images.push({
                    name: image.name,
                    type,
                    path: imagePath,
                })
            }

            imageIndex++
        }

        // Save metadata
        await writeFile(
            join(jobDir, 'metadata.json'),
            JSON.stringify(metadata, null, 2)
        )

        // Trigger generation (async, don't wait)
        triggerGeneration(jobId, metadata).catch(console.error)

        return NextResponse.json({
            success: true,
            jobId,
            message: 'Upload successful, generation started'
        })

    } catch (error) {
        console.error('Upload error:', error)
        return NextResponse.json(
            { error: 'Failed to upload files' },
            { status: 500 }
        )
    }
}

async function triggerGeneration(jobId: string, metadata: any) {
    const apiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000'

    try {
        await fetch(`${apiUrl}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jobId, metadata }),
        })
    } catch (error) {
        console.error('Failed to trigger generation:', error)
    }
}
