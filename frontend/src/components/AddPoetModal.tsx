import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createPoet, type PoetCreateInput } from '../api/client';

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

export function AddPoetModal({ onClose }: Props) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<PoetCreateInput>({
    name: '',
    birth_year: null,
    death_year: null,
    native_place: '',
    style: '',
    biography: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: createPoet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poets'] });
      setSuccess(true);
      setError(null);
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to create poet.';
      setError(msg);
    },
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value === '' ? (name === 'birth_year' || name === 'death_year' ? null : '') : value,
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      setError('诗人名字不能为空');
      return;
    }
    setError(null);
    mutation.mutate({
      ...form,
      birth_year: form.birth_year ? Number(form.birth_year) : null,
      death_year: form.death_year ? Number(form.death_year) : null,
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
          width: 480,
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
          添加诗人
        </h2>

        {success ? (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✓</div>
            <div style={{ fontFamily: 'serif', fontSize: 18, color: '#2d6a2d', marginBottom: 8 }}>
              诗人 "{form.name}" 添加成功！
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 16 }}>
              <button
                onClick={() => { setSuccess(false); setForm({ name: '', birth_year: null, death_year: null, native_place: '', style: '', biography: '' }); }}
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
              <label style={labelStyle}>诗人名字 *</label>
              <input name="name" value={form.name} onChange={handleChange} style={inputStyle} placeholder="例：李白" required />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ ...fieldStyle, flex: 1 }}>
                <label style={labelStyle}>生年</label>
                <input name="birth_year" type="number" value={form.birth_year ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：701" />
              </div>
              <div style={{ ...fieldStyle, flex: 1 }}>
                <label style={labelStyle}>卒年</label>
                <input name="death_year" type="number" value={form.death_year ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：762" />
              </div>
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>籍贯</label>
              <input name="native_place" value={form.native_place ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：陇西成纪" />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>诗风 / 流派</label>
              <input name="style" value={form.style ?? ''} onChange={handleChange} style={inputStyle} placeholder="例：浪漫主义，边塞" />
            </div>

            <div style={fieldStyle}>
              <label style={labelStyle}>简介</label>
              <textarea
                name="biography"
                value={form.biography ?? ''}
                onChange={handleChange}
                style={{ ...inputStyle, minHeight: 80, resize: 'vertical' }}
                placeholder="诗人生平简介…"
              />
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
                {mutation.isPending ? '提交中…' : '添加诗人'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
