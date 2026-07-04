// api/upload.js
import { handleUpload } from "@vercel/blob/client";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const jsonResponse = await handleUpload({
      body: req.body,
      request: req,
      onBeforeGenerateToken: async () => {
        return {
          allowedContentTypes: [
            "application/octet-stream",
            "application/x-gedcom",
            "text/plain"
          ],
          // Ajout d'une limite de sécurité (ex: 200 Mo) 
          // pour protéger votre stockage Blob
          maximumSizeInBytes: 200 * 1024 * 1024 
        };
      },
      onUploadCompleted: async ({ blob }) => {
        console.log("Upload terminé avec succès :", blob.url);
      }
    });

    return res.status(200).json(jsonResponse);
  } catch (error) {
    console.error("Erreur lors de l'upload :", error);
    return res.status(400).json({
      error: error.message || "Upload failed"
    });
  }
}