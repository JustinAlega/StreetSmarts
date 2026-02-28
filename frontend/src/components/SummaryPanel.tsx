/**
 * SummaryPanel — risk breakdown for a selected map location.
 * Owner: Person 4 (Frontend UI + Features)
 *
 * Receives lat/lng from MapView's click handler and fetches location summary.
 */
import { useEffect, useState } from 'react';

interface LocationSummary {
    risk_score: number;
    risk_label: string;
    nearby_posts: number;
    recommendation: string;
    truth: Record<string, number>;
    hotspots: { name: string; risk: number; distance_m: number }[];
}

interface SummaryPanelProps {
    /** The coordinates the user clicked on the map */
    selectedLocation?: { lat: number; lng: number } | null;
}

export default function SummaryPanel({ selectedLocation }: SummaryPanelProps) {
    const [summary, setSummary] = useState<LocationSummary | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!selectedLocation) return;

        // TODO:
        // 1. GET /api/location-summary?lat=...&lng=...&radius=500
        // 2. setSummary(response)
        async function fetchSummary() {
            setLoading(true);
            try {
                // STUB — replace with actual API call
                console.log('Fetching summary for:', selectedLocation);
            } finally {
                setLoading(false);
            }
        }

        fetchSummary();
    }, [selectedLocation]);

    if (!selectedLocation) {
        return (
            <div className="summary-panel">
                <h3>📍 Location Summary</h3>
                <p className="placeholder">Click anywhere on the map to see risk info.</p>
            </div>
        );
    }

    return (
        <div className="summary-panel">
            <h3>📍 Location Summary</h3>

            {loading && <p>Analyzing…</p>}

            {summary && (
                <>
                    {/* TODO: Render risk_score, risk_label, truth breakdown bars, recommendation */}
                    <div className="risk-score">
                        <span className="score">{summary.risk_score}</span>
                        <span className="label">{summary.risk_label}</span>
                    </div>
                    <p className="recommendation">{summary.recommendation}</p>
                    {/* TODO: category breakdown bars */}
                    {/* TODO: hotspots list */}
                </>
            )}
        </div>
    );
}
