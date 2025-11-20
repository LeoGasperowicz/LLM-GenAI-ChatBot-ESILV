export interface ChatMessagePayload {
  user_id?: string;
  message: string;
}

export interface ContextDocument {
  source?: string;
  page?: number | string;
  url?: string;
  snippet?: string;
  [key: string]: any;
}

export type AgentType = "rag_agent" | "form_agent" | "orchestrator" | string;
export type IntentType = "faq" | "contact" | "unknown" | string;

export interface ChatResponse {
  reply: string;
  agent: AgentType;
  intent: IntentType;
  context_documents?: ContextDocument[];
  metadata?: Record<string, any>;
}

export interface AdminStats {
  total_conversations: number;
  total_messages: number;
  top_intents: Record<string, number>;
}

export interface ContactEntry {
  full_name?: string;
  email?: string;
  phone?: string;
  raw_message?: string;
  created_at?: string;
  [key: string]: any;
}

export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
  meta?: any;
}
