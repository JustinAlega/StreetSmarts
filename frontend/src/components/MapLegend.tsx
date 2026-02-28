/**
 * MapLegend — heatmap color legend (green → yellow → red).
 * Owner: Person 4 (Frontend UI + Features)
 *
 * Purely visual — no API calls, no state dependencies.
 */

export default function MapLegend() {
    // TODO: Style this to overlay on the bottom-left of the map
    return (
        <div className="map-legend">
            <h4>Risk Level</h4>
            <div className="legend-bar">
                {/* TODO: CSS gradient bar green→yellow→orange→red */}
                <div className="gradient-bar" />
                <div className="legend-labels">
                    <span>Low</span>
                    <span>Moderate</span>
                    <span>High</span>
                </div>
            </div>
        </div>
    );
}
