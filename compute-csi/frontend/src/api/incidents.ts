import { apiClient } from './client';
import type { IncidentSummary, InvestigationReport, PaginatedResponse, Severity } from '../types';

interface IncidentParams {
  page?: number;
  page_size?: number;
  severity?: Severity;
  status?: string;
}

export async function getIncidents(params: IncidentParams = {}): Promise<PaginatedResponse<IncidentSummary>> {
  const { data } = await apiClient.get<PaginatedResponse<IncidentSummary>>('/api/incidents', { params });
  return data;
}

export async function getIncident(incidentId: string): Promise<InvestigationReport> {
  const { data } = await apiClient.get<InvestigationReport>(`/api/incidents/${incidentId}`);
  return data;
}

export async function investigateIncident(incidentId: string): Promise<InvestigationReport> {
  const { data } = await apiClient.post<InvestigationReport>(`/api/incidents/${incidentId}/investigate`);
  return data;
}

export async function createIncidentForRun(runId: string): Promise<InvestigationReport> {
  const { data } = await apiClient.post<InvestigationReport>(`/api/runs/${runId}/investigate`);
  return data;
}
