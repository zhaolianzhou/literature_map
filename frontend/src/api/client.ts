import axios from 'axios';
import type { Poet, PoetDetail, PoetTrace, Poem, Location, HeatmapPoint, Stats } from '../types';

// BASE_URL is the origin only (no /api suffix).
// - Dev:  falls back to http://localhost:8000
// - Prod: set VITE_API_URL to your backend origin, e.g. https://backend.up.railway.app
//         Leave empty when nginx proxies /api/ to the backend on the same origin.
const BASE_URL = import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== ''
  ? import.meta.env.VITE_API_URL
  : import.meta.env.DEV
    ? 'http://localhost:8000'
    : '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// ── Poets ──────────────────────────────────────────────────────────────────

export async function fetchPoets(): Promise<{ total: number; poets: Poet[] }> {
  const { data } = await api.get('/api/poets/');
  return data;
}

export async function fetchPoet(name: string): Promise<PoetDetail> {
  const { data } = await api.get(`/api/poets/${encodeURIComponent(name)}`);
  return data;
}

export async function fetchPoetTrace(name: string): Promise<PoetTrace> {
  const { data } = await api.get(`/api/poets/${encodeURIComponent(name)}/trace`);
  return data;
}

// ── Poems ──────────────────────────────────────────────────────────────────

export async function fetchPoems(params?: {
  author?: string;
  location?: string;
  skip?: number;
  limit?: number;
}): Promise<{ total: number; poems: Poem[] }> {
  const { data } = await api.get('/api/poems/', { params });
  return data;
}

export async function fetchPoem(id: number): Promise<Poem> {
  const { data } = await api.get(`/api/poems/${id}`);
  return data;
}

// ── Locations ─────────────────────────────────────────────────────────────

export async function fetchLocations(): Promise<{ total: number; locations: Location[] }> {
  const { data } = await api.get('/api/locations/');
  return data;
}

export async function fetchHeatmap(): Promise<{ total: number; heatmap: HeatmapPoint[] }> {
  const { data } = await api.get('/api/locations/heatmap');
  return data;
}

export async function fetchPoemsAtLocation(name: string): Promise<{
  location: Location;
  poem_count: number;
  poems: Poem[];
}> {
  const { data } = await api.get(`/api/locations/${encodeURIComponent(name)}/poems`);
  return data;
}

// ── Stats ─────────────────────────────────────────────────────────────────

export async function fetchStats(): Promise<Stats> {
  const { data } = await api.get('/api/stats');
  return data;
}

// ── Create ─────────────────────────────────────────────────────────────────

export interface PoetCreateInput {
  name: string;
  birth_year?: number | null;
  death_year?: number | null;
  native_place?: string;
  biography?: string;
  style?: string;
}

export interface PoemCreateInput {
  title: string;
  author_name: string;
  dynasty?: string;
  content: string;
  written_year?: number | null;
  occasion?: string;
}

export async function createPoet(input: PoetCreateInput): Promise<Poet & { id: number }> {
  const { data } = await api.post('/api/poets/', input);
  return data;
}

export async function createPoem(input: PoemCreateInput): Promise<{ id: number } & Record<string, unknown>> {
  const { data } = await api.post('/api/poems/', input);
  return data;
}
