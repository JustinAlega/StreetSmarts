/**
 * Utility functions for the location feed.
 */

/**
 * Compute risk level from posts.
 * @param {Array} posts - Array of post objects with severity
 * @returns {'High' | 'Moderate' | 'Low'}
 */
export function computeRisk(posts) {
    if (!posts || posts.length === 0) return 'Low';
    const totalSeverity = posts.reduce((sum, p) => sum + (p.severity || 0), 0);
    if (totalSeverity > 5) return 'High';
    if (totalSeverity > 2) return 'Moderate';
    return 'Low';
}

/**
 * Map risk label to CSS class.
 */
export function riskTone(risk) {
    switch (risk) {
        case 'High': return 'risk-high';
        case 'Moderate': return 'risk-moderate';
        default: return 'risk-low';
    }
}

/**
 * Human-readable relative timestamp.
 */
export function timeAgo(timestamp) {
    if (!timestamp) return 'Unknown';

    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return then.toLocaleDateString();
}

/**
 * Get color for severity value.
 */
export function severityColor(value) {
    if (value >= 0.7) return '#ef4444';
    if (value >= 0.4) return '#f59e0b';
    return '#10b981';
}

/**
 * Get background color for category badge.
 */
export function categoryBadgeStyle(category) {
    const colors = {
        crime: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
        public_safety: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' },
        transport: { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
        infrastructure: { bg: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' },
        policy: { bg: 'rgba(20, 184, 166, 0.15)', color: '#14b8a6' },
        protest: { bg: 'rgba(249, 115, 22, 0.15)', color: '#f97316' },
        weather: { bg: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4' },
        other: { bg: 'rgba(107, 114, 128, 0.15)', color: '#6b7280' },
    };
    return colors[category] || colors.other;
}
