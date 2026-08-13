export type CivitasEnvelope<T> = { success: true; data: T } | { success: false; error: { message: string; code?: string } };
export function unwrapEnvelope<T>(payload: CivitasEnvelope<T>): T { if (!payload.success) throw new Error(payload.error.message); return payload.data; }
