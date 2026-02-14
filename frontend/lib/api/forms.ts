import { request } from "./client";

export interface FormTemplateOut {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  schema: Record<string, unknown>;
  active: boolean;
  stay_active_after_submission: boolean;
  booking_type_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FormSubmissionOut {
  id: string;
  form_template_id: string;
  booking_id: string;
  contact_id: string;
  submitted_at: string;
  answers: Record<string, unknown>;
  created_at: string;
}

export interface FormTemplateCreate {
  name: string;
  description?: string | null;
  schema?: Record<string, unknown>;
  active?: boolean;
  booking_type_id?: string | null;
}

export interface FormTemplateUpdate {
  name?: string;
  description?: string | null;
  schema?: Record<string, unknown>;
  active?: boolean;
  stay_active_after_submission?: boolean;
  booking_type_id?: string | null;
}

// Alias for FormManagement component
export type FormOut = FormTemplateOut;
export type FormUpdate = FormTemplateUpdate;

// Convenience functions for FormManagement component
export function getFormList(workspaceId: string, token?: string) {
  return listFormTemplates(workspaceId, token || "");
}

export function updateFormStatus(workspaceId: string, formId: string, data: FormTemplateUpdate, token?: string) {
  return updateFormTemplate(workspaceId, formId, data, token || "");
}

const base = (workspaceId: string) => `/workspaces/${workspaceId}/forms`;

export function listFormTemplates(workspaceId: string, token: string): Promise<FormTemplateOut[]> {
  return request<FormTemplateOut[]>(base(workspaceId), { token });
}

export function getFormTemplate(
  workspaceId: string,
  templateId: string,
  token: string
): Promise<FormTemplateOut> {
  return request<FormTemplateOut>(`${base(workspaceId)}/${templateId}`, { token });
}

export function createFormTemplate(
  workspaceId: string,
  body: FormTemplateCreate,
  token: string
): Promise<FormTemplateOut> {
  return request<FormTemplateOut>(base(workspaceId), {
    method: "POST",
    body: { ...body, schema: body.schema ?? {} },
    token,
  });
}

export function updateFormTemplate(
  workspaceId: string,
  templateId: string,
  body: FormTemplateUpdate,
  token: string
): Promise<FormTemplateOut> {
  return request<FormTemplateOut>(`${base(workspaceId)}/${templateId}`, {
    method: "PATCH",
    body: body.schema !== undefined ? { ...body, schema: body.schema } : body,
    token,
  });
}

export function deleteFormTemplate(
  workspaceId: string,
  templateId: string,
  token: string
): Promise<void> {
  return request<void>(`${base(workspaceId)}/${templateId}`, { method: "DELETE", token });
}

export function listFormSubmissions(
  workspaceId: string,
  token: string,
  templateId?: string
): Promise<FormSubmissionOut[]> {
  const path = templateId
    ? `${base(workspaceId)}/submissions?template_id=${encodeURIComponent(templateId)}`
    : `${base(workspaceId)}/submissions`;
  return request<FormSubmissionOut[]>(path, { token });
}
