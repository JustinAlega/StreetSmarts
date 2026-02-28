import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const CATEGORIES = [
    'crime', 'public_safety', 'transport', 'infrastructure',
    'policy', 'protest', 'weather', 'other'
];

function getCategoryColor(value) {
    if (value >= 0.6) return '#ef4444';
    if (value >= 0.3) return '#f59e0b';
    return '#10b981';
}

function getRiskClass(score) {
    if (score >= 70) return 'high';
    if (score >= 40) return 'moderate';
    return 'low';
}

function SummaryPanel({ location, onClose }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        if (!location) return;

        setLoading(true);
        fetch(`${API_URL}/location-summary?lat=${location.lat}&lng=${location.lng}`)
            .then(res => res.json())
            .then(d => {
                setData(d);
                setLoading(false);
            })
            .catch(() => {
                setData(null);
                setLoading(false);
            });
    }, [location]);

    if (!location) return null;

    const handleViewFeed = () => {
        const id = encodeURIComponent(
            `${location.name}|${location.lat}|${location.lng}`
        );
        navigate(`/location/${id}`);
    };

    return (
        <div className="summary-panel glass-card">
            <div className="summary-header">
                <div>
                    <div className="summary-title">{location.name}</div>
                    <div className="summary-subtitle">
                        {location.type === 'road' ? '🛣️ Road' : location.type === 'poi' ? '📍 Point of Interest' : '📌 Location'}
                        {' · Saint Louis, MO'}
                    </div>
                </div>
                <button className="close-btn" onClick={onClose}>✕</button>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '32px 0' }}>
                    <div className="loading-spinner" style={{ width: '32px', height: '32px' }}></div>
                    <div style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text-muted)' }}>
                        Analyzing area...
                    </div>
                </div>
            ) : data ? (
                <>
                    {/* Risk Score */}
                    <div className="risk-score-container">
                        <div className={`risk-score-circle ${getRiskClass(data.risk_score)}`}>
                            {Math.round(data.risk_score)}
                        </div>
                        <div className="risk-info">
                            <div className="risk-label" style={{
                                color: data.risk_score >= 70 ? 'var(--danger)' :
                                    data.risk_score >= 40 ? 'var(--moderate)' : 'var(--safe)'
                            }}>
                                {data.risk_label} Risk
                            </div>
                            <div className="risk-recommendation">
                                {data.recommendation}
                            </div>
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="risk-progress">
                        <div
                            className="risk-progress-bar"
                            style={{
                                width: `${Math.min(100, data.risk_score)}%`,
                                background: data.risk_score >= 70 ? 'linear-gradient(90deg, #f59e0b, #ef4444)' :
                                    data.risk_score >= 40 ? 'linear-gradient(90deg, #10b981, #f59e0b)' :
                                        'linear-gradient(90deg, #10b981, #34d399)',
                            }}
                        />
                    </div>

                    {/* Stats */}
                    <div className="stats-row">
                        <div className="stat-card">
                            <div className="stat-value">{data.report_count}</div>
                            <div className="stat-label">Reports</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{data.radius_km} km</div>
                            <div className="stat-label">Radius</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{data.hotspots?.length || 0}</div>
                            <div className="stat-label">Hotspots</div>
                        </div>
                    </div>

                    {/* Category Breakdown */}
                    <div className="category-breakdown">
                        <h3>Category Breakdown</h3>
                        {CATEGORIES.map(cat => {
                            const value = data.categories?.[cat] || 0;
                            return (
                                <div key={cat} className="category-bar">
                                    <span className="category-name">{cat.replace('_', ' ')}</span>
                                    <div className="category-track">
                                        <div
                                            className="category-fill"
                                            style={{
                                                width: `${Math.min(100, value * 100)}%`,
                                                background: getCategoryColor(value),
                                            }}
                                        />
                                    </div>
                                    <span className="category-value">{(value * 100).toFixed(0)}%</span>
                                </div>
                            );
                        })}
                    </div>

                    {/* Hotspots */}
                    {data.hotspots && data.hotspots.length > 0 && (
                        <div className="hotspots">
                            {data.hotspots.map((h, i) => (
                                <span
                                    key={i}
                                    className="hotspot-badge"
                                    style={{
                                        background: h.score >= 0.6 ? 'var(--danger-bg)' :
                                            h.score >= 0.3 ? 'var(--moderate-bg)' : 'var(--safe-bg)',
                                        color: h.score >= 0.6 ? 'var(--danger)' :
                                            h.score >= 0.3 ? 'var(--moderate)' : 'var(--safe)',
                                    }}
                                >
                                    {h.category.replace('_', ' ')}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* CTA */}
                    <button className="summary-cta" onClick={handleViewFeed}>
                        See Live Incidents →
                    </button>
                </>
            ) : (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: '13px' }}>
                    No data available for this location yet.
                </div>
            )}
        </div>
    );
}

export default SummaryPanel;
