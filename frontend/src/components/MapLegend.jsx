function MapLegend() {
    return (
        <div className="map-legend glass">
            <div className="legend-title">Risk Level</div>
            <div className="legend-gradient"></div>
            <div className="legend-labels">
                <span>Safe</span>
                <span>Moderate</span>
                <span>Caution</span>
                <span>Avoid</span>
            </div>
        </div>
    );
}

export default MapLegend;
