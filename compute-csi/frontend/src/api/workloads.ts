import { apiClient } from './client';
import type { StartRunRequest, StartRunResponse } from '../types';

export async function startRun(request: StartRunRequest): Promise<StartRunResponse> {
  const { data } = await apiClient.post<StartRunResponse>('/api/workloads/run', request);
  return data;
}
