/**
 * RoutePanel — start/end inputs, safety slider, route button.
 * Owner: Person 3 (Frontend Map + Routing)
 *
 * Communicates route coordinates back to App/MapView via callback.
 */
import { useState } from 'react';

interface RoutePanelProps {
    /** Called with the route coordinates returned by the API */
    onRouteReceived?: (coords: [number, number][]) => void;
}

export default function RoutePanel({ onRouteReceived }: RoutePanelProps) {
    const [startAddr, setStartAddr] = useState('');
    const [endAddr, setEndAddr] = useState('');
    const [lambda, setLambda] = useState(0.5);
    const [loading, setLoading] = useState(false);

    async function handleRoute() {
        // TODO:
        // 1. Geocode startAddr and endAddr to [lng, lat] (Mapbox Geocoding API)
        // 2. POST /api/route with { start, end, lambda_val: lambda }
        // 3. Call onRouteReceived(response.coordinates)
        setLoading(true);
        try {
            // STUB — replace with actual API call
            console.log('Route request:', { startAddr, endAddr, lambda });
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="route-panel">
            <h3>🧭 Route Planner</h3>

            <label>
                Start
                <input
                    type="text"
                    placeholder="e.g. Gateway Arch"
                    value={startAddr}
                    onChange={(e) => setStartAddr(e.target.value)}
                />
            </label>

            <label>
                Destination
                <input
                    type="text"
                    placeholder="e.g. Delmar Loop"
                    value={endAddr}
                    onChange={(e) => setEndAddr(e.target.value)}
                />
            </label>

            <label>
                Safety priority: {Math.round(lambda * 100)}%
                <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={lambda}
                    onChange={(e) => setLambda(parseFloat(e.target.value))}
                />
                <span className="range-labels">
                    <span>Shortest</span>
                    <span>Safest</span>
                </span>
            </label>

            <button onClick={handleRoute} disabled={loading}>
                {loading ? 'Finding route…' : 'Get Safe Route'}
            </button>
        </div>
    );
}
