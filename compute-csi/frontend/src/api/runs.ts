import { apiClient } from './client';
import type { RunSummary, RunDetail, RunMetrics, PaginatedResponse } from '../types';

export async function getRuns(page = 1, pageSize = 20): Promise<PaginatedResponse<RunSummary>> {
  const { data } = await apiClient.get<PaginatedResponse<RunSummary>>('/api/runs', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getRun(runId: string): Promise<RunDetail> {
  const { data } = await apiClient.get<RunDetail>(`/api/runs/${runId}`);
  return data;
}

export async function cancelRun(runId: string): Promise<void> {
  await apiClient.post(`/api/runs/${runId}/cancel`);
}

export async function getRunTimeline(runId: string): Promise<RunDetail> {
  const { data } = await apiClient.get<RunDetail>(`/api/runs/${runId}/timeline`);
  return data;
}

export async function getRunMetrics(runId: string): Promise<RunMetrics> {
  const { data } = await apiClient.get<RunMetrics>(`/api/runs/${runId}/metrics`);
  return data;
}
