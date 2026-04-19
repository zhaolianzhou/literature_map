import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPoets, fetchPoetTrace } from '../api/client';
import type { Poet, TracePoint } from '../types';
import { POET_COLORS } from './TraceMap';

interface PoetPanelProps {
  selectedPoets: string[];
  onTogglePoet: (name: string, color: string) => void;
  onTracePointSelect: (pt: TracePoint, poet: string) => void;
  poetColorMap: Record<string, string>;
}

export function PoetPanel({
  selectedPoets,
  onTogglePoet,
  onTracePointSelect,
  poetColorMap,
}: PoetPanelProps) {
  const [search, setSearch] = useState('');
  const [activePoet, setActivePoet] = useState<string | null>(null);

  const { data: poetsData } = useQuery({
    queryKey: ['poets'],
    queryFn: fetchPoets,
    staleTime: 5 * 60 * 1000,   // treat data as fresh for 5 min
    gcTime: Infinity,            // never evict from cache while the app is open
  });

  const { data: traceData } = useQuery({
    queryKey: ['trace', activePoet],
    queryFn: () => fetchPoetTrace(activePoet!),
    enabled: !!activePoet,
  });

  const filteredPoets = (poetsData?.poets ?? []).filter((p) =>
    p.name.includes(search) || (p.style ?? '').includes(search)
  );

  const styleColors: Record<string, string> = {
    '浪漫主义': '#e74c3c',
    '现实主义': '#3498db',
    '山水田园': '#2ecc71',
    '边塞': '#e67e22',
    '朦胧婉约': '#9b59b6',
    '怀古咏史': '#8e44ad',
  };

  const getStyleBadge = (style?: string) => {
    const color = style ? (styleColors[style] ?? '#95a5a6') : '#95a5a6';
    return (
      <span
        style={{
          background: color,
          color: '#fff',
          borderRadius: 12,
          padding: '1px 8px',
          fontSize: 10,
          fontWeight: 600,
        }}
      >
        {style ?? ''}
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Search */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #eee' }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索诗人…"
          style={{
            width: '100%',
            padding: '6px 10px',
            borderRadius: 6,
            border: '1px solid #ddd',
            fontSize: 13,
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Poet list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filteredPoets.map((poet: Poet, idx) => {
          const isSelected = selectedPoets.includes(poet.name);
          const color = poetColorMap[poet.name] ?? POET_COLORS[idx % POET_COLORS.length];
          const isActive = activePoet === poet.name;

          return (
            <div
              key={poet.name}
              style={{
                borderBottom: '1px solid #f0f0f0',
                background: isActive ? '#f8f9ff' : '#fff',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '8px 12px',
                  gap: 8,
                  cursor: 'pointer',
                }}
                onClick={() => setActivePoet(isActive ? null : poet.name)}
              >
                {/* Colour checkbox */}
                <div
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePoet(poet.name, color);
                  }}
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 4,
                    background: isSelected ? color : '#ddd',
                    cursor: 'pointer',
                    flexShrink: 0,
                    border: `2px solid ${color}`,
                    transition: 'background 0.2s',
                  }}
                  title={isSelected ? '取消显示' : '在地图上显示轨迹'}
                />

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 14, fontFamily: 'serif' }}>
                      {poet.name}
                    </span>
                    {getStyleBadge(poet.style)}
                  </div>
                  <div style={{ fontSize: 11, color: '#999', marginTop: 1 }}>
                    {poet.birth_year && poet.death_year
                      ? `${poet.birth_year}–${poet.death_year} AD`
                      : poet.birth_year
                      ? `b. ${poet.birth_year} AD`
                      : ''}{' '}
                    · {poet.poem_count} 首
                  </div>
                </div>

                <span style={{ fontSize: 10, color: '#ccc' }}>{isActive ? '▲' : '▼'}</span>
              </div>

              {/* Expanded trace list */}
              {isActive && traceData && traceData.poet === poet.name && (
                <div
                  style={{
                    paddingLeft: 40,
                    paddingRight: 12,
                    paddingBottom: 8,
                    background: '#f8f9ff',
                  }}
                >
                  <p style={{ fontSize: 11, color: '#666', margin: '4px 0 8px' }}>
                    {traceData.biography}
                  </p>
                  <div style={{ fontSize: 11, color: '#888', marginBottom: 6 }}>
                    行迹 {traceData.trace_count} 处：
                  </div>
                  {traceData.trace.map((pt, i) => (
                    <div
                      key={i}
                      onClick={() => onTracePointSelect(pt, poet.name)}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 6,
                        marginBottom: 6,
                        cursor: 'pointer',
                        padding: '4px 6px',
                        borderRadius: 4,
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={(e) =>
                        ((e.currentTarget as HTMLDivElement).style.background = '#e8f0fe')
                      }
                      onMouseLeave={(e) =>
                        ((e.currentTarget as HTMLDivElement).style.background = 'transparent')
                      }
                    >
                      <span
                        style={{
                          minWidth: 18,
                          height: 18,
                          borderRadius: '50%',
                          background: color,
                          color: '#fff',
                          fontSize: 9,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 12 }}>
                          {pt.location.name}
                        </div>
                        <div style={{ fontSize: 10, color: '#888' }}>
                          《{pt.poem_title}》{pt.year ? ` · ${pt.year} AD` : ''}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
