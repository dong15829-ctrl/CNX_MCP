"use client";

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ChartData,
    ChartOptions
} from 'chart.js';
import { Chart } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface ChartRendererProps {
    type: 'line' | 'bar' | 'doughnut' | 'pie';
    data: ChartData;
    options?: ChartOptions;
}

export default function ChartRenderer({ type, data, options }: ChartRendererProps) {
    const defaultOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
                labels: {
                    color: '#a1a1aa', // var(--text-secondary)
                    font: {
                        family: 'Inter'
                    }
                }
            },
            title: {
                display: false,
            },
        },
        scales: type === 'doughnut' || type === 'pie' ? undefined : {
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                },
                ticks: {
                    color: '#a1a1aa',
                }
            },
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    color: '#a1a1aa',
                }
            }
        }
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return (
        <div style={{ width: '100%', height: '100%', minHeight: '300px' }}>
            <Chart type={type} data={data} options={mergedOptions} />
        </div>
    );
}
