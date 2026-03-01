import { useState, useRef } from 'react';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// STL proximity bias for geocoding
const STL_PROXIMITY = '-90.1994,38.6270';

function RoutePanel({ onRouteComputed, onResetRoute }) {
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

    const handleClearRoute = () => {
        setStartText('');
        setEndText('');
        setStartCoords(null);
        setEndCoords(null);
        setRouteResult(null);
        setError(null);
        setStartSuggestions([]);
        setEndSuggestions([]);
        onResetRoute();
    };

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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <svg viewBox="0 0 24 24" fill="none" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 12H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12ZM16 8L9.5 9.5L8 16L14.5 14.5L16 8Z" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Route Planner
                    </span>
                </h2>
                {routeResult && (
                    <button
                        onClick={handleClearRoute}
                        style={{
                            background: 'rgba(255,255,255,0.1)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            padding: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--text-secondary, #aaa)',
                            transition: 'color 0.2s, background 0.2s',
                        }}
                        title="Clear route"
                        onMouseEnter={e => { e.currentTarget.style.color = '#fff'; e.currentTarget.style.background = 'rgba(239,68,68,0.5)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-secondary, #aaa)'; e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" width="18" height="18">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
            </div>

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
                    <svg className="route-input-icon end" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" width="16" height="16">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                    </svg>
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
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14" style={{ marginRight: '4px' }}>
                        <path fillRule="evenodd" d="M12 1.5a5.25 5.25 0 0 0-5.25 5.25v3a3 3 0 0 0-3 3v6.75a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3v-6.75a3 3 0 0 0-3-3v-3c0-2.9-2.35-5.25-5.25-5.25Zm3.75 8.25v-3a3.75 3.75 0 1 0-7.5 0v3h7.5Z" clipRule="evenodd" />
                    </svg>
                    Safety First
                </button>
                <button
                    id="priority-speed-btn"
                    className={`priority-btn ${priority === 'speed' ? 'active' : ''}`}
                    onClick={() => setPriority('speed')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14" style={{ marginRight: '4px' }}>
                        <path fillRule="evenodd" d="M14.615 1.595a.75.75 0 0 1 .359.852L12.982 9.75h7.268a.75.75 0 0 1 .548 1.262l-10.5 11.25a.75.75 0 0 1-1.272-.71l1.992-7.302H3.75a.75.75 0 0 1-.548-1.262l10.5-11.25a.75.75 0 0 1 .913-.143Z" clipRule="evenodd" />
                    </svg>
                    Fastest
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
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <svg viewBox="0 0 24 24" fill="none" width="16" height="16" xmlns="http://www.w3.org/2000/svg"><path d="M5 17H19C21 17 22 16 22 14V10C22 8 21 7 19 7H5C3 7 2 8 2 10V14C2 16 3 17 5 17Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><path d="M18 7V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><path d="M6 7V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><path d="M10.05 7L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><path d="M14 7V10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
                            Distance
                        </span>
                        <span>{routeResult.distance_m >= 1000
                            ? `${(routeResult.distance_m / 1000).toFixed(1)} km`
                            : `${Math.round(routeResult.distance_m)} m`
                        }</span>
                    </div>
                    {routeResult.duration_min && (
                        <div className="route-result-row">
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <svg viewBox="0 0 24 24" fill="none" width="16" height="16" xmlns="http://www.w3.org/2000/svg"><path d="M12 7V12L13.5 14.5M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                                Walking time
                            </span>
                            <span>{Math.round(routeResult.duration_min)} min</span>
                        </div>
                    )}
                    {routeResult.risk_score != null && (
                        <div className="route-result-row">
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <svg viewBox="0 0 24 24" fill="none" width="16" height="16" xmlns="http://www.w3.org/2000/svg"><path d="M9 12L11 14L15 9.99999M20 12C20 16.4611 14.54 19.6937 12.6414 20.683C12.4361 20.79 12.3334 20.8435 12.191 20.8712C12.08 20.8928 11.92 20.8928 11.809 20.8712C11.6666 20.8435 11.5639 20.79 11.3586 20.683C9.45996 19.6937 4 16.4611 4 12V8.21759C4 7.41808 4 7.01833 4.13076 6.6747C4.24627 6.37113 4.43398 6.10027 4.67766 5.88552C4.9535 5.64243 5.3278 5.50207 6.0764 5.22134L11.4382 3.21067C11.6461 3.13271 11.75 3.09373 11.857 3.07827C11.9518 3.06457 12.0482 3.06457 12.143 3.07827C12.25 3.09373 12.3539 3.13271 12.5618 3.21067L17.9236 5.22134C18.6722 5.50207 19.0465 5.64243 19.3223 5.88552C19.566 6.10027 19.7537 6.37113 19.8692 6.6747C20 7.01833 20 7.41808 20 8.21759V12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                                Route risk
                            </span>
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
