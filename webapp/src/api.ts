import { BACKEND_BASE_URL } from "./config";
import type {
  ChatMessagePayload,
  ChatResponse,
  AdminStats,
  ContactEntry
} from "./types";

async function handleResponse(res: Response) {
  if (!res.ok) {
    let detail: any;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new Error(`Erreur API (${res.status}): ${JSON.stringify(detail)}`);
  }
  try {
    return await res.json();
  } catch {
    return await res.text();
  }
}

export async function apiChat(payload: ChatMessagePayload): Promise<ChatResponse> {
  const res = await fetch(`${BACKEND_BASE_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return handleResponse(res);
}

export async function apiGetStats(): Promise<AdminStats> {
  const res = await fetch(`${BACKEND_BASE_URL}/admin/stats`);
  return handleResponse(res);
}

export async function apiGetContacts(): Promise<ContactEntry[]> {
  const res = await fetch(`${BACKEND_BASE_URL}/admin/contacts`);
  return handleResponse(res);
}
