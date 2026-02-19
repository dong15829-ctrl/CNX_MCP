"use client";

import MetricCard from '../../components/MetricCard';
import ChartRenderer from '../../components/ChartRenderer';
import { Share2, ThumbsUp, MessageCircle } from 'lucide-react';
import { ChartData } from 'chart.js';

export default function SocialPage() {
    const lineData: ChartData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
            {
                label: 'Engagement Rate',
                data: [4.2, 4.5, 3.8, 5.1, 4.9, 5.5, 6.0],
                borderColor: '#ec4899',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                tension: 0.4,
                fill: true
            }
        ]
    };

    return (
        <div>
            <h1 style={{ marginBottom: '2rem' }}>Social Media Analytics</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
                <MetricCard label="Total Likes" value="45.2k" change="8%" trend="up" icon={<ThumbsUp />} color="#3b82f6" />
                <MetricCard label="Shares" value="12.5k" change="15%" trend="up" icon={<Share2 />} color="#8b5cf6" />
                <MetricCard label="Comments" value="3,840" change="-4%" trend="down" icon={<MessageCircle />} color="#ec4899" />
            </div>

            <div className="glass-panel" style={{ padding: '2rem', height: '400px' }}>
                <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Weekly Engagement Trend</h3>
                <ChartRenderer type="line" data={lineData} />
            </div>
        </div>
    );
}
