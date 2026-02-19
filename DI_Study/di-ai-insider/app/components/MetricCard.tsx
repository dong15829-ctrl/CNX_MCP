import { ArrowUp, ArrowDown } from 'lucide-react';
import clsx from 'clsx';

interface MetricCardProps {
    label: string;
    value: string;
    change: string;
    trend: 'up' | 'down';
    icon?: React.ReactNode;
    color?: string; // Hex for neon glow
}

export default function MetricCard({ label, value, change, trend, icon, color = '#3b82f6' }: MetricCardProps) {
    return (
        <div className="glass-panel" style={{
            padding: '1.5rem',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Glow effect */}
            <div style={{
                position: 'absolute',
                top: '-20px',
                right: '-20px',
                width: '100px',
                height: '100px',
                background: color,
                opacity: 0.1,
                borderRadius: '50%',
                filter: 'blur(40px)'
            }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>
                {icon && <div style={{ color: color }}>{icon}</div>}
            </div>

            <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                {value}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.875rem' }}>
                {trend === 'up' ? <ArrowUp size={16} color="#10b981" /> : <ArrowDown size={16} color="#ef4444" />}
                <span style={{ color: trend === 'up' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                    {change}
                </span>
                <span style={{ color: 'var(--text-muted)' }}>vs last month</span>
            </div>
        </div>
    );
}
