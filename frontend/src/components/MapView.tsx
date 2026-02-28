/**
 * MapView — Mapbox GL map with heatmap layer + route line + click handler.
 * Owner: Person 3 (Frontend Map + Routing)
 *
 * This is the main map component. Nobody else should edit this file.
 * Other components communicate via props/callbacks, not by touching MapView.
 */
import { useEffect, useRef } from 'react';

// TODO: import mapboxgl from 'mapbox-gl' once node_modules installed

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
const STL_CENTER: [number, number] = [-90.199, 38.627];
const DEFAULT_ZOOM = 12;

interface MapViewProps {
    /** Called when user clicks the map — pass lat/lng to SummaryPanel */
    onLocationClick?: (lat: number, lng: number) => void;
    /** Route coordinates to draw as a polyline [[lng, lat], ...] */
    routeCoords?: [number, number][];
}

export default function MapView({ onLocationClick, routeCoords }: MapViewProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<any>(null);

    useEffect(() => {
        // TODO: Initialize Mapbox GL map
        // 1. mapboxgl.accessToken = MAPBOX_TOKEN
        // 2. new mapboxgl.Map({ container, center: STL_CENTER, zoom: DEFAULT_ZOOM, style: 'mapbox://styles/mapbox/dark-v11' })
        // 3. On map load: fetch /api/heatmap-data, add GeoJSON source, add heatmap layer
        // 4. On map click: call onLocationClick(lat, lng)
        // 5. Cleanup on unmount

        return () => {
            // mapRef.current?.remove();
        };
    }, []);

    useEffect(() => {
        // TODO: When routeCoords changes, draw/update route polyline layer
        // 1. If source 'route' exists, update data
        // 2. Else add source + line layer
    }, [routeCoords]);

    return (
        <div
            ref={mapContainer}
            className="mapview"
            style={{ width: '100%', height: '100%' }}
        >
            {/* Map renders here */}
            <p style={{ padding: '2rem', color: '#888' }}>
                🗺️ MapView — Mapbox map will render here (needs VITE_MAPBOX_TOKEN)
            </p>
        </div>
    );
}
