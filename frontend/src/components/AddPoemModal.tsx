import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createPoem, fetchPoets, type PoemCreateInput } from '../api/client';

interface Props {
  onClose: () => void;
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 10px',
  border: '1px solid #d0c8be',
  borderRadius: 6,
  fontSize: 14,
  fontFamily: 'inherit',
  boxSizing: 'border-box',
  background: '#faf8f5',
  outline: 'none',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 600,
  color: '#555',
  marginBottom: 4,
};

const fieldStyle: React.CSSProperties = {
  marginBottom: 14,
};

const emptyForm = (): PoemCreateInput => ({
  title: '',
  author_name: '',
  dynasty: '唐',
  content: '',
  written_year: null,
  occasion: '',
});

export function AddPoemModal({ onClose }: Props) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<PoemCreateInput>(emptyForm());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const { data: poetsData } = useQuery({ queryKey: ['poets'], queryFn: fetchPoets, staleTime: Infinity });
  const poetNames = poetsData?.poets.map((p) => p.name) ?? [];

  const mutation = useMutation({
    mutationFn: createPoem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poems'] });
      setSuccess(true);
      setError(null);
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to create poem.';
      setError(msg);
    },
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value === '' && name === 'written_year' ? null : value,
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) { setError('诗题不能为空'); return; }
    if (!form.author_name.trim()) { setError('请选择或输入诗人名'); return; }
    if (!form.content.trim()) { setError('诗文内容不能为空'); return; }
    setError(null);
    mutation.mutate({
      ...form,
      written_year: form.written_year ? Number(form.written_year) : null,
    });
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.45)',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          width: 520,
          maxWidth: '95vw',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '28px 32px',
          boxShadow: '0 8px 40px rgba(0,0,0,0.25)',
          position: 'relative',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 16,
            right: 18,
            background: 'none',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: '#888',
            lineHeight: 1,
          }}
          aria-label="Close"
        >
          ✕
        </button>

        <h2 style={{ margin: '0 0 20px', fontFamily: 'serif', fontSize: 20, color: '#1a1a2e' }}>
          添加诗作
        </h2>

        {success ? (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✓</div>
            <div style={{ fontFamily: 'serif', fontSize: 18, color: '#2d6a2d', marginBottom: 8 }}>
              《{form.title}》添加成功！
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 16 }}>
              <button
                onClick={() => { setSuccess(false); setForm(emptyForm()); }}
                style={{ padding: '8px 20px', borderRadius: 6, border: '1px solid #1a1a2e', background: '#fff', cursor: 'pointer', fontSize: 13 }}
              >
                继续添加
              </button>
              <button
                onClick={onClose}
                style={{ padding: '8px 20px', borderRadius: 6, border: 'none', background: '#1a1a2e', color: '#f5c842', cursor: 'pointer', fontSize: 13 }}
              >
                完成
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={fieldStyle}>
              <label style={labelStyle}>诗题 *</label>
              <input name="title" value={form.title} onChange={handleChange} style={inputStyle} placeholder="例：静夜思" required />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>诗人 *</label>
              {poetNames.length > 0 ? (
                <select name="author_name" value={form.author_name} onChange={handleChange} style={inputStyle}>
                  <option value="">— 请选择诗人 —</option>
                  {poetNames.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              ) : (
                <input name="author_name" value={form.author_name} onChange={handleChange} style={inputStyle} placeholder="诗人名字" />
              )}
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ ...fieldStyle, flex: 1 }}>
                <label style={labelStyle}>朝代</label>
                <input name="dynasty" value={form.dynasty ?? ''} onChange={handleChange} style={inputStyle} placeholder="唐" />
              </div>
              <div style={{ ...fieldStyle, flex: 1 }}>
                <label style={labelStyle}>创作年份</label>
                <input name="written_year" type="number" value={form.written_year ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：726" />
              </div>
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>诗文内容 *</label>
              <textarea
                name="content"
                value={form.content}
                onChange={handleChange}
                style={{ ...inputStyle, minHeight: 120, resize: 'vertical', fontFamily: 'serif', lineHeight: 1.8 }}
                placeholder="床前明月光，疑是地上霜…"
                required
              />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>创作背景 / 场合</label>
              <input name="occasion" value={form.occasion ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：寓居扬州思乡" />
            </div>

            {error && (
              <div style={{ color: '#c0392b', fontSize: 13, marginBottom: 12, background: '#fdf2f0', padding: '8px 12px', borderRadius: 6 }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button type="button" onClick={onClose} style={{ padding: '8px 20px', borderRadius: 6, border: '1px solid #ccc', background: '#fff', cursor: 'pointer', fontSize: 13 }}>
                取消
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                style={{
                  padding: '8px 24px',
                  borderRadius: 6,
                  border: 'none',
                  background: mutation.isPending ? '#888' : '#1a1a2e',
                  color: '#f5c842',
                  cursor: mutation.isPending ? 'not-allowed' : 'pointer',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {mutation.isPending ? '提交中…' : '添加诗作'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
