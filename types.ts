
export interface Landmark {
  id: string;
  name: string;
  description: string;
  imageUrl: string;
  category: 'ثقافي' | 'ترفيهي' | 'تاريخي' | 'تسوق';
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  images?: string[];
}

export interface GroundingMetadata {
  web?: { uri: string; title: string };
  maps?: { uri: string; title: string };
}
