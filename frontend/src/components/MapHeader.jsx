function MapHeader({ heatmapActive, safeActive, safeLoading, onToggleHeatmap, onToggleSafe }) {
    return (
        <div className="map-header glass">
            <div className="header-brand">
                <span className="brand-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path fillRule="evenodd" d="M12 1.5a5.25 5.25 0 0 0-5.25 5.25v3a3 3 0 0 0-3 3v6.75a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3v-6.75a3 3 0 0 0-3-3v-3c0-2.9-2.35-5.25-5.25-5.25Zm3.75 8.25v-3a3.75 3.75 0 1 0-7.5 0v3h7.5Z" clipRule="evenodd" /></svg></span>
                <span>Street<span style={{ color: '#4a4a4a' }}>Smarts</span></span>
            </div>

            <button
                id="heatmap-toggle-btn"
                className={`header-btn ${heatmapActive ? 'active' : ''}`}
                onClick={onToggleHeatmap}
            >
                <span className="btn-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path fillRule="evenodd" d="M12.963 2.286a.75.75 0 0 0-1.071-.136 9.742 9.742 0 0 0-3.539 6.176 7.547 7.547 0 0 1-1.705-1.715.75.75 0 0 0-1.152-.082A9 9 0 1 0 15.68 4.534a7.46 7.46 0 0 1-2.717-2.248ZM15.75 14.25a3.75 3.75 0 1 1-7.313-1.172c.628.465 1.35.81 2.133 1a5.99 5.99 0 0 1 1.925-3.546 3.75 3.75 0 0 1 3.255 3.718Z" clipRule="evenodd" /></svg></span>
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
                        <span className="btn-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path fillRule="evenodd" d="M12 1.5a5.25 5.25 0 0 0-5.25 5.25v3a3 3 0 0 0-3 3v6.75a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3v-6.75a3 3 0 0 0-3-3v-3c0-2.9-2.35-5.25-5.25-5.25Zm3.75 8.25v-3a3.75 3.75 0 1 0-7.5 0v3h7.5Z" clipRule="evenodd" /></svg></span>
                        Safe Spaces
                    </>
                )}
            </button>

        </div>
    );
}

export default MapHeader;
