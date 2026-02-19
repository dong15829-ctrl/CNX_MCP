import Link from 'next/link';
import { ArrowRight, BarChart3, PieChart, Activity } from 'lucide-react';

export default function Home() {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingTop: '4rem' }}>
      <header style={{ marginBottom: '4rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>
          Welcome to <span className="text-gradient">AI INSIDER</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>
          The Ultimate Dynamic Marketing Intelligence Dashboard
        </p>
      </header>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '2rem'
      }}>
        {/* Card 1 */}
        <Link href="/dashboard/overview" className="glass-panel" style={{ padding: '2rem', textDecoration: 'none', color: 'inherit' }}>
          <div style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            <Activity size={32} />
          </div>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1.5rem' }}>Overview</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Comprehensive view of all marketing channels and KPIs.
          </p>
        </Link>

        {/* Card 2 */}
        <Link href="/dashboard/playground" className="glass-panel" style={{ padding: '2rem', textDecoration: 'none', color: 'inherit' }}>
          <div style={{ marginBottom: '1rem', color: 'var(--accent-purple)' }}>
            <BarChart3 size={32} />
          </div>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1.5rem' }}>Playground</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            <strong style={{ color: 'var(--accent-pink)' }}>Make it yours.</strong> Paste data and visualize instantly.
          </p>
        </Link>

        {/* Card 3 */}
        <Link href="/dashboard/campaigns" className="glass-panel" style={{ padding: '2rem', textDecoration: 'none', color: 'inherit' }}>
          <div style={{ marginBottom: '1rem', color: 'var(--accent-pink)' }}>
            <PieChart size={32} />
          </div>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1.5rem' }}>Campaigns</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Deep dive into ad performance and ROAS analytics.
          </p>
        </Link>
      </div>
    </div>
  );
}
