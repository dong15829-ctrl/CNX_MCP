"use client";

import MetricCard from '../../components/MetricCard';
import ChartRenderer from '../../components/ChartRenderer';
import { Target, TrendingUp, DollarSign, BarChart } from 'lucide-react';
import { ChartData } from 'chart.js';

export default function CampaignsPage() {
    const barData: ChartData = {
        labels: ['Google Ads', 'Facebook', 'LinkedIn', 'Instagram', 'TikTok'],
        datasets: [
            {
                label: 'Spend',
                data: [5000, 4200, 1500, 3000, 2000],
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 4
            },
            {
                label: 'Revenue',
                data: [12000, 8000, 2000, 4500, 1800],
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }
        ]
    };

    const doughnutData: ChartData = {
        labels: ['Awareness', 'Consideration', 'Conversion', 'Retention'],
        datasets: [
            {
                data: [40, 30, 20, 10],
                backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981'],
                borderWidth: 0
            }
        ]
    };

    return (
        <div>
            <h1 style={{ marginBottom: '2rem' }}>Campaign Performance</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
                <MetricCard label="Total Spend" value="$15,700" change="5%" trend="up" icon={<DollarSign />} color="#ef4444" />
                <MetricCard label="ROAS" value="3.8x" change="-2%" trend="down" icon={<TrendingUp />} color="#10b981" />
                <MetricCard label="Conversions" value="1,240" change="10%" trend="up" icon={<Target />} color="#3b82f6" />
                <MetricCard label="CTR" value="2.1%" change="0.5%" trend="up" icon={<BarChart />} color="#8b5cf6" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                <div className="glass-panel" style={{ padding: '2rem', height: '400px' }}>
                    <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Spend vs Revenue</h3>
                    <ChartRenderer type="bar" data={barData} />
                </div>

                <div className="glass-panel" style={{ padding: '2rem', height: '400px' }}>
                    <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Funnel Distribution</h3>
                    <ChartRenderer type="doughnut" data={doughnutData} />
                </div>
            </div>
        </div>
    );
}
