"use client";

import { useState, useEffect } from 'react';
import ChartRenderer from '../../components/ChartRenderer';
import { AlertCircle, Play, Save } from 'lucide-react';

const DEFAULT_DATA = {
    type: 'bar',
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
        {
            label: 'Revenue 2024',
            data: [12000, 19000, 3000, 5000, 2000, 3000],
            backgroundColor: 'rgba(59, 130, 246, 0.6)',
            borderColor: '#3b82f6',
            borderWidth: 1,
        },
        {
            label: 'Target',
            data: [10000, 15000, 8000, 10000, 5000, 7000],
            backgroundColor: 'rgba(236, 72, 153, 0.6)',
            borderColor: '#ec4899',
            borderWidth: 1,
        }
    ]
};

export default function PlaygroundPage() {
    const [jsonInput, setJsonInput] = useState(JSON.stringify(DEFAULT_DATA, null, 2));
    const [parsedData, setParsedData] = useState<any>(DEFAULT_DATA);
    const [error, setError] = useState<string | null>(null);

    const handleParse = () => {
        try {
            const parsed = JSON.parse(jsonInput);

            // Basic validation
            if (!parsed.datasets || !parsed.labels) {
                throw new Error("Invalid Format: JSON must contain 'labels' and 'datasets'.");
            }

            setParsedData(parsed);
            setError(null);
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h1 style={{ marginBottom: '1.5rem' }}>Dynamic Playground</h1>
            <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
                Edit the JSON data on the left to instantly update the chart on the right.
                Supports <code>type: 'bar' | 'line' | 'doughnut'</code>.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', height: 'calc(100vh - 200px)' }}>

                {/* Editor Section */}
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{
                        padding: '1rem',
                        borderBottom: '1px solid var(--border-color)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        background: 'rgba(0,0,0,0.2)'
                    }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>INPUT DATA (JSON)</span>
                        <button
                            onClick={handleParse}
                            style={{
                                background: 'var(--gradient-main)',
                                border: 'none',
                                color: 'white',
                                padding: '0.5rem 1rem',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                fontWeight: 600
                            }}
                        >
                            <Play size={16} /> Render
                        </button>
                    </div>

                    <div style={{ position: 'relative', flex: 1 }}>
                        <textarea
                            value={jsonInput}
                            onChange={(e) => setJsonInput(e.target.value)}
                            style={{
                                width: '100%',
                                height: '100%',
                                background: 'transparent',
                                color: '#d4d4d8',
                                border: 'none',
                                padding: '1rem',
                                fontFamily: 'monospace',
                                fontSize: '14px',
                                resize: 'none',
                                outline: 'none',
                                lineHeight: '1.5'
                            }}
                            spellCheck={false}
                        />
                    </div>

                    {error && (
                        <div style={{
                            padding: '1rem',
                            background: 'rgba(220, 38, 38, 0.2)',
                            color: '#f87171',
                            borderTop: '1px solid rgba(220, 38, 38, 0.5)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            <AlertCircle size={16} />
                            {error}
                        </div>
                    )}
                </div>

                {/* Preview Section */}
                <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ marginBottom: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        Live Preview
                    </h3>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <ChartRenderer
                            type={parsedData.type || 'bar'}
                            data={{ labels: parsedData.labels, datasets: parsedData.datasets }}
                        />
                    </div>
                </div>

            </div>
        </div>
    );
}
