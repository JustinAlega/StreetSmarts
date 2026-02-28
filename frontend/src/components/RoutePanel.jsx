import { useState, useRef } from 'react';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// STL proximity bias for geocoding
const STL_PROXIMITY = '-90.1994,38.6270';

function RoutePanel({ onRouteComputed }) {
    const [startText, setStartText] = useState('');
    const [endText, setEndText] = useState('');
    const [startCoords, setStartCoords] = useState(null);
    const [endCoords, setEndCoords] = useState(null);
    const [startSuggestions, setStartSuggestions] = useState([]);
    const [endSuggestions, setEndSuggestions] = useState([]);
    const [priority, setPriority] = useState('safety');
    const [loading, setLoading] = useState(false);
    const [routeResult, setRouteResult] = useState(null);
    const [error, setError] = useState(null);
    const [showStartDropdown, setShowStartDropdown] = useState(false);
    const [showEndDropdown, setShowEndDropdown] = useState(false);
    const startTimeout = useRef(null);
    const endTimeout = useRef(null);

    const geocode = async (query) => {
        if (!query || query.length < 3) return [];
        try {
            const res = await fetch(
                `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&proximity=${STL_PROXIMITY}&bbox=-90.5,38.4,-90.0,38.85&limit=5`
            );
            const data = await res.json();
            return data.features || [];
        } catch {
            return [];
        }
    };

    const handleStartChange = (e) => {
        const val = e.target.value;
        setStartText(val);
        setStartCoords(null);
        setRouteResult(null);
        setError(null);
        clearTimeout(startTimeout.current);
        startTimeout.current = setTimeout(async () => {
            const results = await geocode(val);
            setStartSuggestions(results);
            setShowStartDropdown(results.length > 0);
        }, 300);
    };

    const handleEndChange = (e) => {
        const val = e.target.value;
        setEndText(val);
        setEndCoords(null);
        setRouteResult(null);
        setError(null);
        clearTimeout(endTimeout.current);
        endTimeout.current = setTimeout(async () => {
            const results = await geocode(val);
            setEndSuggestions(results);
            setShowEndDropdown(results.length > 0);
        }, 300);
    };

    const selectStartSuggestion = (feature) => {
        setStartText(feature.place_name);
        setStartCoords(feature.center);
        setShowStartDropdown(false);
        setStartSuggestions([]);
    };

    const selectEndSuggestion = (feature) => {
        setEndText(feature.place_name);
        setEndCoords(feature.center);
        setShowEndDropdown(false);
        setEndSuggestions([]);
    };

    const handleSubmit = async () => {
        if (!startCoords || !endCoords) return;
        setLoading(true);
        setError(null);
        setRouteResult(null);

        try {
            const res = await fetch(`${API_URL}/route`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_lat: startCoords[1],
                    start_lng: startCoords[0],
                    end_lat: endCoords[1],
                    end_lng: endCoords[0],
                    priority,
                }),
            });
            const data = await res.json();
            if (data.error) {
                setError(data.error);
            } else if (data.coordinates) {
                onRouteComputed(data);
                setRouteResult(data);
            }
        } catch (err) {
            console.error('Route error:', err);
            setError('Failed to compute route. Check if the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="route-panel glass">
            <h2>
                <span>🧭 Route Planner</span>
            </h2>

            <div className="route-input-group">
                <div className="route-input-wrapper">
                    <div className="route-input-dot start"></div>
                    <input
                        id="route-start-input"
                        className="route-input"
                        type="text"
                        placeholder="Start location..."
                        value={startText}
                        onChange={handleStartChange}
                        onFocus={() => startSuggestions.length > 0 && setShowStartDropdown(true)}
                        onBlur={() => setTimeout(() => setShowStartDropdown(false), 200)}
                    />
                    {showStartDropdown && (
                        <div className="autocomplete-dropdown">
                            {startSuggestions.map((f, i) => (
                                <div
                                    key={i}
                                    className="autocomplete-item"
                                    onMouseDown={() => selectStartSuggestion(f)}
                                >
                                    {f.place_name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="route-input-wrapper">
                    <div className="route-input-dot end"></div>
                    <input
                        id="route-end-input"
                        className="route-input"
                        type="text"
                        placeholder="Destination..."
                        value={endText}
                        onChange={handleEndChange}
                        onFocus={() => endSuggestions.length > 0 && setShowEndDropdown(true)}
                        onBlur={() => setTimeout(() => setShowEndDropdown(false), 200)}
                    />
                    {showEndDropdown && (
                        <div className="autocomplete-dropdown">
                            {endSuggestions.map((f, i) => (
                                <div
                                    key={i}
                                    className="autocomplete-item"
                                    onMouseDown={() => selectEndSuggestion(f)}
                                >
                                    {f.place_name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <div className="priority-selector">
                <button
                    id="priority-safety-btn"
                    className={`priority-btn ${priority === 'safety' ? 'active' : ''}`}
                    onClick={() => setPriority('safety')}
                >
                    🛡️ Safety First
                </button>
                <button
                    id="priority-speed-btn"
                    className={`priority-btn ${priority === 'speed' ? 'active' : ''}`}
                    onClick={() => setPriority('speed')}
                >
                    ⚡ Fastest
                </button>
            </div>

            <button
                id="route-submit-btn"
                className="route-submit"
                onClick={handleSubmit}
                disabled={!startCoords || !endCoords || loading}
            >
                {loading ? (
                    <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                        <span className="loading-spinner"></span> Computing...
                    </span>
                ) : (
                    'Find Safe Route'
                )}
            </button>

            {/* Route result info */}
            {routeResult && (
                <div className="route-result">
                    <div className="route-result-row">
                        <span>📏 Distance</span>
                        <span>{routeResult.distance_m >= 1000
                            ? `${(routeResult.distance_m / 1000).toFixed(1)} km`
                            : `${Math.round(routeResult.distance_m)} m`
                        }</span>
                    </div>
                    {routeResult.duration_min && (
                        <div className="route-result-row">
                            <span>🕐 Walking time</span>
                            <span>{Math.round(routeResult.duration_min)} min</span>
                        </div>
                    )}
                    {routeResult.risk_score != null && (
                        <div className="route-result-row">
                            <span>🛡️ Route risk</span>
                            <span style={{
                                color: routeResult.risk_score >= 60 ? 'var(--danger)' :
                                    routeResult.risk_score >= 30 ? 'var(--moderate)' : 'var(--safe)'
                            }}>
                                {routeResult.risk_score.toFixed(0)}%
                            </span>
                        </div>
                    )}
                </div>
            )}

            {error && (
                <div style={{
                    marginTop: '12px', padding: '8px 12px',
                    background: 'rgba(239, 68, 68, 0.15)', borderRadius: '8px',
                    color: '#ef4444', fontSize: '12px'
                }}>
                    {error}
                </div>
            )}
        </div>
    );
}

export default RoutePanel;
