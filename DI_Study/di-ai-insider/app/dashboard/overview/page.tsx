"use client";

import MetricCard from '../../components/MetricCard';
import ChartRenderer from '../../components/ChartRenderer';
import { Users, DollarSign, MousePointer, Eye } from 'lucide-react';
import { ChartData } from 'chart.js';

export default function OverviewPage() {
    const lineChartData: ChartData = {
        labels: ['Day 1', 'Day 7', 'Day 14', 'Day 21', 'Day 28'],
        datasets: [
            {
                label: 'Total Visits',
                data: [150, 300, 450, 400, 600],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Unique Users',
                data: [100, 220, 350, 320, 500],
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                fill: true,
                tension: 0.4
            }
        ]
    };

    return (
        <div>
            <h1 style={{ marginBottom: '2rem' }}>Marketing Overview</h1>

            {/* Metrics Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '1.5rem',
                marginBottom: '2rem'
            }}>
                <MetricCard
                    label="Total Revenue"
                    value="$54,230"
                    change="12%"
                    trend="up"
                    icon={<DollarSign size={24} />}
                    color="#10b981"
                />
                <MetricCard
                    label="Active Users"
                    value="8.1k"
                    change="24%"
                    trend="up"
                    icon={<Users size={24} />}
                    color="#3b82f6"
                />
                <MetricCard
                    label="Conversion Rate"
                    value="3.2%"
                    change="1.2%"
                    trend="down"
                    icon={<MousePointer size={24} />}
                    color="#ec4899"
                />
                <MetricCard
                    label="Impressions"
                    value="142k"
                    change="8%"
                    trend="up"
                    icon={<Eye size={24} />}
                    color="#8b5cf6"
                />
            </div>

            {/* Main Chart Section */}
            <div className="glass-panel" style={{ padding: '2rem', minHeight: '400px' }}>
                <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Traffic Trends</h3>
                <ChartRenderer type="line" data={lineChartData} />
            </div>

            {/* Recent Activity / Table (Optional Placeholder) */}
            <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                <div className="glass-panel" style={{ padding: '2rem', height: '300px' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Top Campaigns</h3>
                    <table style={{ width: '100%', borderCollapse: 'collapse', color: 'var(--text-secondary)' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                                <th style={{ padding: '0.5rem' }}>Name</th>
                                <th style={{ padding: '0.5rem' }}>Status</th>
                                <th style={{ padding: '0.5rem' }}>Revenue</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td style={{ padding: '0.5rem' }}>Black Friday</td><td style={{ color: '#10b981' }}>Active</td><td>$12,000</td></tr>
                            <tr><td style={{ padding: '0.5rem' }}>Holiday Promo</td><td style={{ color: '#fbbf24' }}>Paused</td><td>$8,500</td></tr>
                            <tr><td style={{ padding: '0.5rem' }}>New User Bonus</td><td style={{ color: '#10b981' }}>Active</td><td>$4,200</td></tr>
                        </tbody>
                    </table>
                </div>

                <div className="glass-panel" style={{ padding: '2rem', height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ textAlign: 'center' }}>
                        <h3 style={{ marginBottom: '1rem' }}>Target Reached</h3>
                        <div style={{
                            width: '150px',
                            height: '150px',
                            borderRadius: '50%',
                            background: 'conic-gradient(var(--accent-primary) 70%, rgba(255,255,255,0.1) 0)',
                            margin: '0 auto',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '2rem',
                            fontWeight: 700
                        }}>
                            70%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
