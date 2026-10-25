import { apiClient } from './client';
import type { DashboardSummary, IntegrationsStatus } from '../types';

export async function getDashboard(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>('/api/dashboard');
  return data;
}

export async function getIntegrationsStatus(): Promise<IntegrationsStatus> {
  const { data } = await apiClient.get<IntegrationsStatus>('/api/integrations/status');
  return data;
}
