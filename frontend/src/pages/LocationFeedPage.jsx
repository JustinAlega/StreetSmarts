import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { computeRisk, riskTone, timeAgo, severityColor, categoryBadgeStyle } from '../lib/locationFeed';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function LocationFeedPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [posts, setPosts] = useState([]);
    const [activeTab, setActiveTab] = useState('feed');
    const [composerText, setComposerText] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [loading, setLoading] = useState(true);

    // Parse location from encoded ID
    const parts = decodeURIComponent(id).split('|');
    const locationName = parts[0] || 'Unknown Location';
    const lat = parseFloat(parts[1]) || 38.6270;
    const lng = parseFloat(parts[2]) || -90.1994;

    const fetchFeed = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/feed?lat=${lat}&lng=${lng}&radius_km=2`);
            const data = await res.json();
            setPosts(data.posts || []);
        } catch (err) {
            console.error('Feed error:', err);
        } finally {
            setLoading(false);
        }
    }, [lat, lng]);

    useEffect(() => {
        fetchFeed();
        // Auto-refresh every 15 seconds
        const interval = setInterval(fetchFeed, 15000);
        return () => clearInterval(interval);
    }, [fetchFeed]);

    const handleSubmitPost = async () => {
        if (!composerText.trim()) return;
        setSubmitting(true);

        try {
            await fetch(`${API_URL}/post`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat,
                    lng,
                    content: composerText,
                }),
            });
            setComposerText('');
            await fetchFeed();
        } catch (err) {
            console.error('Post error:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const risk = computeRisk(posts);
    const riskClass = riskTone(risk);

    return (
        <div className="feed-page">
            {/* Header */}
            <div className="feed-header">
                <button className="feed-back-btn" onClick={() => navigate('/')}>
                    ← Back to Map
                </button>

                <div className="feed-header-content">
                    <div>
                        <div className="feed-location-name">{locationName}</div>
                        <div className="feed-stats">
                            <span className="feed-stat">
                                📊 {posts.length} reports
                            </span>
                            <span className="feed-stat">
                                📍 {lat.toFixed(4)}, {lng.toFixed(4)}
                            </span>
                        </div>
                    </div>
                    <span className={`feed-risk-badge ${riskClass}`}>
                        {risk} Risk
                    </span>
                </div>
            </div>

            {/* Tabs */}
            <div className="feed-tabs">
                <button
                    className={`feed-tab ${activeTab === 'feed' ? 'active' : ''}`}
                    onClick={() => setActiveTab('feed')}
                >
                    Live Feed
                </button>
                <button
                    className={`feed-tab ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    Summary
                </button>
            </div>

            {/* Content */}
            <div className="feed-content">
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '48px 0' }}>
                        <div className="loading-spinner" style={{ width: '32px', height: '32px' }}></div>
                        <div style={{ marginTop: '12px', color: 'var(--text-muted)', fontSize: '13px' }}>
                            Loading reports...
                        </div>
                    </div>
                ) : activeTab === 'feed' ? (
                    <>
                        {posts.length === 0 ? (
                            <div style={{
                                textAlign: 'center', padding: '48px 0',
                                color: 'var(--text-muted)', fontSize: '14px'
                            }}>
                                <div style={{ fontSize: '48px', marginBottom: '12px' }}>🔍</div>
                                No reports in this area yet.<br />
                                Be the first to share an update!
                            </div>
                        ) : (
                            posts.map((post, i) => {
                                const badgeStyle = categoryBadgeStyle(post.category);
                                return (
                                    <div key={post.id || i} className="post-card">
                                        <div className="post-meta">
                                            <span
                                                className="post-badge"
                                                style={{
                                                    background: badgeStyle.bg,
                                                    color: badgeStyle.color,
                                                }}
                                            >
                                                {(post.category || 'other').replace('_', ' ')}
                                            </span>
                                            <span className="post-time">
                                                {post.human ? '👤' : '🤖'} · {timeAgo(post.created_at)}
                                                {post.distance_km != null && ` · ${post.distance_km.toFixed(1)} km`}
                                            </span>
                                        </div>
                                        <div className="post-content">{post.content}</div>
                                        <div className="post-severity-bar">
                                            <div
                                                className="post-severity-fill"
                                                style={{
                                                    width: `${Math.min(100, (post.severity || 0) * 100)}%`,
                                                    background: severityColor(post.severity || 0),
                                                }}
                                            />
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </>
                ) : (
                    <div style={{ padding: '16px 0' }}>
                        <div className="risk-score-container">
                            <div className={`risk-score-circle ${risk === 'High' ? 'high' : risk === 'Moderate' ? 'moderate' : 'low'}`}>
                                {posts.length}
                            </div>
                            <div className="risk-info">
                                <div className="risk-label" style={{
                                    color: risk === 'High' ? 'var(--danger)' : risk === 'Moderate' ? 'var(--moderate)' : 'var(--safe)'
                                }}>
                                    {risk} Activity Level
                                </div>
                                <div className="risk-recommendation">
                                    {posts.length} reports within 2km of this location.
                                    {risk === 'High' && ' Exercise heightened caution in this area.'}
                                    {risk === 'Moderate' && ' Stay aware of your surroundings.'}
                                    {risk === 'Low' && ' Area appears relatively calm.'}
                                </div>
                            </div>
                        </div>

                        {/* Category summary */}
                        <div className="category-breakdown" style={{ marginTop: '16px' }}>
                            <h3>Report Categories</h3>
                            {['crime', 'public_safety', 'transport', 'infrastructure', 'other'].map(cat => {
                                const count = posts.filter(p => p.category === cat).length;
                                const ratio = posts.length > 0 ? count / posts.length : 0;
                                return (
                                    <div key={cat} className="category-bar">
                                        <span className="category-name">{cat.replace('_', ' ')}</span>
                                        <div className="category-track">
                                            <div
                                                className="category-fill"
                                                style={{
                                                    width: `${ratio * 100}%`,
                                                    background: severityColor(ratio),
                                                }}
                                            />
                                        </div>
                                        <span className="category-value">{count}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Composer */}
            <div className="feed-composer">
                <textarea
                    id="feed-composer-textarea"
                    className="composer-textarea"
                    placeholder="Report a safety observation for this area..."
                    value={composerText}
                    onChange={(e) => setComposerText(e.target.value)}
                />
                <div className="composer-actions">
                    <button
                        id="feed-submit-btn"
                        className="composer-submit"
                        onClick={handleSubmitPost}
                        disabled={!composerText.trim() || submitting}
                    >
                        {submitting ? (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span className="loading-spinner"></span> Submitting...
                            </span>
                        ) : (
                            'Submit Report'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default LocationFeedPage;
