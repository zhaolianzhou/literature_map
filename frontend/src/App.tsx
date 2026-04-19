import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TraceMap, POET_COLORS } from './components/TraceMap';
import { PoetPanel } from './components/PoetPanel';
import { PoemDetail } from './components/PoemDetail';
import { AddPoetModal } from './components/AddPoetModal';
import { AddPoemModal } from './components/AddPoemModal';
import { fetchPoetTrace, fetchHeatmap, fetchStats } from './api/client';
import type { TracePoint } from './types';
import './App.css';

export default function App() {
  const [selectedPoets, setSelectedPoets] = useState<string[]>([]);
  const [poetColorMap, setPoetColorMap] = useState<Record<string, string>>({});
  const [traceData, setTraceData] = useState<
    { poet: string; trace: TracePoint[]; color: string }[]
  >([]);
  const [selectedPoint, setSelectedPoint] = useState<{ pt: TracePoint; poet: string } | null>(
    null
  );
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showAddPoet, setShowAddPoet] = useState(false);
  const [showAddPoem, setShowAddPoem] = useState(false);

  const { data: stats } = useQuery({ queryKey: ['stats'], queryFn: fetchStats });
  const { data: heatmapData } = useQuery({
    queryKey: ['heatmap'],
    queryFn: fetchHeatmap,
    enabled: showHeatmap,
  });

  const handleTogglePoet = useCallback(
    async (name: string, color: string) => {
      const isSelected = selectedPoets.includes(name);

      if (isSelected) {
        setSelectedPoets((prev) => prev.filter((p) => p !== name));
        setTraceData((prev) => prev.filter((t) => t.poet !== name));
      } else {
        const colorIdx = selectedPoets.length % POET_COLORS.length;
        const assignedColor = color || POET_COLORS[colorIdx];
        setPoetColorMap((prev) => ({ ...prev, [name]: assignedColor }));
        setSelectedPoets((prev) => [...prev, name]);

        const trace = await fetchPoetTrace(name);
        setTraceData((prev) => [
          ...prev,
          { poet: name, trace: trace.trace, color: assignedColor },
        ]);
      }
    },
    [selectedPoets]
  );

  const handleTracePointSelect = useCallback((pt: TracePoint, poet: string) => {
    setSelectedPoint({ pt, poet });
    setSelectedLocation(null);
  }, []);

  const handleLocationClick = useCallback((name: string) => {
    setSelectedLocation(name);
    setSelectedPoint(null);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedPoint(null);
    setSelectedLocation(null);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f5f0eb' }}>
      {/* Header */}
      <header
        style={{
          background: '#1a1a2e',
          color: '#f5c842',
          padding: '0 20px',
          height: 52,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          flexShrink: 0,
          zIndex: 100,
        }}
      >
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          style={{
            background: 'none',
            border: 'none',
            color: '#f5c842',
            cursor: 'pointer',
            fontSize: 20,
            padding: 0,
            lineHeight: 1,
          }}
          title="侧栏"
        >
          ☰
        </button>

        <div style={{ fontFamily: 'serif', fontSize: 18, fontWeight: 700, letterSpacing: 2 }}>
          唐诗行迹地图
        </div>
        <div style={{ fontSize: 12, color: '#aaa', fontFamily: 'sans-serif' }}>
          Ancient China Literature Travel Map
        </div>

        <div style={{ flex: 1 }} />

        {stats && (
          <div
            style={{
              display: 'flex',
              gap: 16,
              fontSize: 11,
              color: '#ccc',
              fontFamily: 'sans-serif',
            }}
          >
            <span>诗 {stats.total_poems}</span>
            <span>诗人 {stats.total_poets}</span>
            <span>地名 {stats.total_locations_db}</span>
          </div>
        )}

        <button
          onClick={() => setShowAddPoet(true)}
          style={{
            background: 'transparent',
            color: '#f5c842',
            border: '1px solid #f5c842',
            borderRadius: 6,
            padding: '4px 12px',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          + 添加诗人
        </button>

        <button
          onClick={() => setShowAddPoem(true)}
          style={{
            background: 'transparent',
            color: '#f5c842',
            border: '1px solid #f5c842',
            borderRadius: 6,
            padding: '4px 12px',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          + 添加诗作
        </button>

        <button
          onClick={() => setShowHeatmap((v) => !v)}
          style={{
            background: showHeatmap ? '#f5c842' : 'transparent',
            color: showHeatmap ? '#1a1a2e' : '#f5c842',
            border: '1px solid #f5c842',
            borderRadius: 6,
            padding: '4px 12px',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          {showHeatmap ? '关闭热力图' : '显示热力图'}
        </button>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        {sidebarOpen && (
          <aside
            style={{
              width: 280,
              background: '#fff',
              borderRight: '1px solid #e0d8cf',
              display: 'flex',
              flexDirection: 'column',
              flexShrink: 0,
              overflowY: 'hidden',
            }}
          >
            <div
              style={{
                padding: '10px 12px 6px',
                fontSize: 11,
                color: '#888',
                fontWeight: 600,
                letterSpacing: 1,
                borderBottom: '1px solid #eee',
                textTransform: 'uppercase',
              }}
            >
              诗人列表
            </div>
            <PoetPanel
              selectedPoets={selectedPoets}
              onTogglePoet={handleTogglePoet}
              onTracePointSelect={handleTracePointSelect}
              poetColorMap={poetColorMap}
            />
          </aside>
        )}

        {/* Map */}
        <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <TraceMap
            traces={traceData}
            heatmap={heatmapData?.heatmap}
            showHeatmap={showHeatmap}
            onLocationClick={handleLocationClick}
            onTracePointClick={handleTracePointSelect}
          />

          {/* Legend */}
          {!showHeatmap && traceData.length > 0 && (
            <div
              style={{
                position: 'absolute',
                top: 12,
                left: 12,
                background: 'rgba(255,255,255,0.92)',
                borderRadius: 8,
                padding: '8px 12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                zIndex: 500,
                fontSize: 12,
                fontFamily: 'serif',
              }}
            >
              {traceData.map(({ poet, color }) => (
                <div
                  key={poet}
                  style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}
                >
                  <span
                    style={{
                      width: 20,
                      height: 3,
                      background: color,
                      display: 'inline-block',
                      borderRadius: 2,
                    }}
                  />
                  {poet}
                </div>
              ))}
            </div>
          )}

          {/* Detail overlay */}
          <PoemDetail
            selectedPoint={selectedPoint}
            selectedLocation={selectedLocation}
            onClose={handleCloseDetail}
          />

          {traceData.length === 0 && !showHeatmap && (
            <div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                pointerEvents: 'none',
                zIndex: 500,
              }}
            >
              <div
                style={{
                  background: 'rgba(255,255,255,0.88)',
                  borderRadius: 12,
                  padding: '24px 32px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                }}
              >
                <div style={{ fontSize: 36, marginBottom: 8 }}>🗺</div>
                <div style={{ fontFamily: 'serif', fontSize: 18, color: '#333', marginBottom: 4 }}>
                  唐诗三百首 · 行迹地图
                </div>
                <div style={{ fontSize: 13, color: '#888' }}>
                  在左侧选择诗人，查看其诗歌足迹
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {showAddPoet && <AddPoetModal onClose={() => setShowAddPoet(false)} />}
      {showAddPoem && <AddPoemModal onClose={() => setShowAddPoem(false)} />}
    </div>
  );
}
