function MapHeader({ heatmapActive, safeActive, safeLoading, onToggleHeatmap, onToggleSafe, onResetRoute }) {
    return (
        <div className="map-header glass">
            <div className="header-brand">
                <span className="brand-icon">🧠</span>
                StreetSmarts
            </div>

            <button
                id="heatmap-toggle-btn"
                className={`header-btn ${heatmapActive ? 'active' : ''}`}
                onClick={onToggleHeatmap}
            >
                <span className="btn-icon">🔥</span>
                Heatmap
            </button>

            <button
                id="safe-toggle-btn"
                className={`header-btn ${safeActive ? 'active' : ''} ${safeLoading ? 'loading' : ''}`}
                onClick={onToggleSafe}
                disabled={safeLoading}
            >
                {safeLoading ? (
                    <>
                        <span className="btn-spinner"></span>
                        Loading…
                    </>
                ) : (
                    <>
                        <span className="btn-icon">🛡️</span>
                        Nearby Safe
                    </>
                )}
            </button>

            <button
                id="reset-route-btn"
                className="header-btn"
                onClick={onResetRoute}
            >
                <span className="btn-icon">🔄</span>
                Reset Route
            </button>
        </div>
    );
}

export default MapHeader;
