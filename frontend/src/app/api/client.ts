/**
 * API client for CMMC Compliance Platform backend.
 * All requests go through the Vite dev proxy (localhost:8001).
 */

const ORG_ID = '9de53b587b23450b87af';

async function fetchJSON(url: string, options?: RequestInit) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try { detail = JSON.parse(text).detail || text; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

async function fetchBlob(url: string): Promise<Blob> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  return res.blob();
}

function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ── Health ──
export async function getHealth() {
  return fetchJSON('/health');
}

// ── Scoring / Overview ──
export async function getComplianceOverview() {
  return fetchJSON(`/api/scoring/overview?org_id=${ORG_ID}`);
}

export async function getGaps() {
  return fetchJSON(`/api/scoring/gaps?org_id=${ORG_ID}`);
}

// ── POA&M ──
export async function getPoamSummary() {
  return fetchJSON(`/api/scoring/poam?org_id=${ORG_ID}`);
}

export async function generatePoam() {
  return fetchJSON(`/api/scoring/poam/generate?org_id=${ORG_ID}`, { method: 'POST' });
}

export async function exportPoamPdf() {
  const blob = await fetchBlob(`/api/scoring/poam/export-pdf?org_id=${ORG_ID}`);
  triggerDownload(blob, `POAM_Apex_Defense_${new Date().toISOString().slice(0,10)}.pdf`);
}

export async function exportPoamDocx() {
  const blob = await fetchBlob(`/api/scoring/poam/export-docx?org_id=${ORG_ID}`);
  triggerDownload(blob, `POAM_Apex_Defense_${new Date().toISOString().slice(0,10)}.docx`);
}

// ── SSP ──
export async function generateFullSSP() {
  return fetchJSON('/api/ssp/generate-full', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ org_profile: { org_id: ORG_ID }, export_docx: true }),
  });
}

export async function getSSPJobStatus(jobId: string) {
  return fetchJSON(`/api/ssp/status?job_id=${jobId}`);
}

export async function exportSSPAsPdf() {
  const blob = await fetchBlob(`/api/ssp/export-pdf?org_id=${ORG_ID}`);
  triggerDownload(blob, `SSP_Apex_Defense_${new Date().toISOString().slice(0,10)}.pdf`);
}

export async function exportSSPAsDocx() {
  const blob = await fetchBlob('/api/ssp/export-latest');
  triggerDownload(blob, `SSP_Apex_Defense_${new Date().toISOString().slice(0,10)}.docx`);
}

export async function getSSPNarrative(controlId: string) {
  return fetchJSON(`/api/ssp/narrative/${controlId}`);
}

// ── Evidence ──
export async function listArtifacts(state?: string | null, limit = 500) {
  let url = `/api/evidence/?org_id=${ORG_ID}&limit=${limit}`;
  if (state) url += `&state=${state}`;
  return fetchJSON(url);
}

export async function previewArtifact(id: string) {
  return fetchJSON(`/api/evidence/${id}/preview`);
}

export async function uploadEvidence(file: File, metadata: Record<string, string>) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('org_id', ORG_ID);
  Object.entries(metadata).forEach(([k, v]) => { if (v) formData.append(k, v); });
  const res = await fetch('/api/evidence/upload', { method: 'POST', body: formData });
  if (!res.ok) { const t = await res.text(); throw new Error(t); }
  return res.json();
}

export async function transitionArtifact(id: string, newState: string) {
  return fetchJSON(`/api/evidence/${id}/transition?new_state=${newState}`, { method: 'POST' });
}

export async function downloadArtifact(id: string, filename?: string) {
  const blob = await fetchBlob(`/api/evidence/${id}/download`);
  triggerDownload(blob, filename || 'download');
}

export async function getEvidenceByControl(controlId: string) {
  return fetchJSON(`/api/evidence/by-control/${controlId}`);
}

export async function linkEvidenceToControls(artifactId: string, controlIds: string[]) {
  return fetchJSON(`/api/evidence/${artifactId}/link-controls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ control_ids: controlIds }),
  });
}

export async function verifyAuditChain() {
  return fetchJSON('/api/evidence/audit/verify');
}

export async function generateManifest() {
  return fetchJSON('/api/evidence/manifest/generate', { method: 'POST' });
}

export async function downloadManifest() {
  const blob = await fetchBlob('/api/evidence/manifest/download');
  triggerDownload(blob, `MANIFEST_${new Date().toISOString().slice(0,10)}.txt`);
}

// ── Intake ──
export async function createIntakeSession() {
  return fetchJSON('/api/intake/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ org_id: ORG_ID }),
  });
}

export async function getIntakeModule(sessionId: string, moduleId: number) {
  return fetchJSON(`/api/intake/sessions/${sessionId}/module/${moduleId}`);
}

export async function saveIntakeResponses(sessionId: string, answers: any[]) {
  return fetchJSON(`/api/intake/sessions/${sessionId}/responses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  });
}

export async function getCompanyProfile() {
  return fetchJSON(`/api/intake/company-profile/${ORG_ID}`);
}

// ── Documents ──
export async function listDocumentTemplates() {
  return fetchJSON('/api/documents/templates');
}

export async function generateDocument(docType: string) {
  return fetchJSON(`/api/documents/generate/${docType}`, { method: 'POST' });
}

export async function listGeneratedDocuments() {
  return fetchJSON('/api/documents');
}
