
import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";

const API_KEY = process.env.API_KEY || "";

export class GeminiService {
  private ai: GoogleGenAI;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: API_KEY });
  }

  async askAboutKuwait(prompt: string, location?: { latitude: number, longitude: number }) {
    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
        config: {
          systemInstruction: "أنت خبير في شؤون دولة الكويت. أجب باللغة العربية بأسلوب ودود ومعلوماتي. استخدم أدوات البحث والخرائط لتزويد المستخدم بأحدث المعلومات والمواقع الجغرافية الدقيقة.",
          tools: [{ googleSearch: {} }, { googleMaps: {} }],
          ...(location && {
            toolConfig: {
              retrievalConfig: {
                latLng: {
                  latitude: location.latitude,
                  longitude: location.longitude
                }
              }
            }
          })
        }
      });

      return {
        text: response.text,
        grounding: response.candidates?.[0]?.groundingMetadata?.groundingChunks || []
      };
    } catch (error) {
      console.error("Gemini Error:", error);
      throw error;
    }
  }

  async generateKuwaitImage(prompt: string) {
    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-2.5-flash-image',
        contents: {
          parts: [{ text: `A high-quality, realistic photograph of ${prompt} in Kuwait City, architectural photography, vibrant colors, 4k.` }]
        },
        config: {
          imageConfig: {
            aspectRatio: "16:9"
          }
        }
      });

      let imageUrl = "";
      for (const part of response.candidates?.[0]?.content?.parts || []) {
        if (part.inlineData) {
          imageUrl = `data:image/png;base64,${part.inlineData.data}`;
          break;
        }
      }
      return imageUrl;
    } catch (error) {
      console.error("Image Generation Error:", error);
      throw error;
    }
  }
}

export const geminiService = new GeminiService();
