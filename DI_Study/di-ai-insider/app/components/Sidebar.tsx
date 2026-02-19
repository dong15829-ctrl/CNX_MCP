"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    BarChart3,
    Home,
    Settings,
    PieChart,
    Activity,
    Layers,
    Terminal
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
    { name: 'Overview', href: '/dashboard/overview', icon: Activity },
    { name: 'Campaigns', href: '/dashboard/campaigns', icon: PieChart },
    { name: 'Social Media', href: '/dashboard/social', icon: Layers },
    { name: 'Playground', href: '/dashboard/playground', icon: Terminal },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="glass-panel" style={{
            width: '260px',
            margin: '1rem',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100vh - 2rem)',
            position: 'sticky',
            top: '1rem'
        }}>
            <div style={{ marginBottom: '3rem', padding: '0 0.5rem' }}>
                <Link href="/" style={{ textDecoration: 'none' }}>
                    <h2 className="text-gradient" style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <BarChart3 /> AI INSIDER
                    </h2>
                </Link>
            </div>

            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={clsx(
                                "nav-item",
                                isActive && "active"
                            )}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.75rem 1rem',
                                borderRadius: 'var(--radius-sm)',
                                textDecoration: 'none',
                                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                                background: isActive ? 'rgba(255,255,255,0.05)' : 'transparent',
                                border: isActive ? '1px solid var(--border-glow)' : '1px solid transparent',
                                transition: 'all 0.2s ease'
                            }}
                        >
                            <Icon size={20} color={isActive ? 'var(--accent-primary)' : 'currentColor'} />
                            <span style={{ fontWeight: isActive ? 600 : 400 }}>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            <div style={{ padding: '0 0.5rem' }}>
                <button style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    cursor: 'pointer',
                    padding: '0.75rem 0'
                }}>
                    <Settings size={20} />
                    Settings
                </button>
            </div>
        </aside>
    );
}
