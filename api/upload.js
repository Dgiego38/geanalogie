import { put } from '@vercel/blob';

export default async function handler(req, res) {

    if (req.method !== 'POST') {
        return res.status(405).json({
            error: 'Method not allowed'
        });
    }

    const blob = await put(
        `gedcom-${Date.now()}.ged`,
        req,
        {
            access: 'public'
        }
    );

    return res.status(200).json({
        url: blob.url
    });
}