import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Saint Louis center
const STL_CENTER = [-90.1994, 38.6270];
const STL_ZOOM = 12.5;

// Categories to search for safe locations (Mapbox POI categories)
const SAFE_POI_SEARCHES = [
    { query: 'police station', icon: '🚔', color: '#3b82f6', label: 'Police Station' },
    { query: 'fire station', icon: '🚒', color: '#ef4444', label: 'Fire Station' },
    { query: 'hospital', icon: '🏥', color: '#10b981', label: 'Hospital' },
    { query: 'pharmacy', icon: '💊', color: '#8b5cf6', label: 'Pharmacy' },
    { query: 'library', icon: '📚', color: '#6366f1', label: 'Library' },
];

/**
 * Reverse geocode a coordinate to get the street/place name.
 */
async function reverseGeocode(lat, lng) {
    try {
        const res = await fetch(
            `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?access_token=${MAPBOX_TOKEN}&types=address,poi,neighborhood,locality&limit=1`
        );
        const data = await res.json();
        if (data.features && data.features.length > 0) {
            const feat = data.features[0];
            // For address type, get the short name (street name)
            if (feat.place_type?.includes('address')) {
                return feat.text || feat.place_name.split(',')[0];
            }
            return feat.text || feat.place_name.split(',')[0];
        }
    } catch (e) {
        console.warn('Reverse geocode failed:', e);
    }
    return null;
}

/**
 * Fetch real safe POIs near the center using Mapbox Places API.
 */
async function fetchSafePOIs(centerLng, centerLat) {
    const allPOIs = [];

    for (const poiType of SAFE_POI_SEARCHES) {
        try {
            const res = await fetch(
                `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(poiType.query)}.json?access_token=${MAPBOX_TOKEN}&proximity=${centerLng},${centerLat}&bbox=${centerLng - 0.06},${centerLat - 0.04},${centerLng + 0.06},${centerLat + 0.04}&limit=5`
            );
            const data = await res.json();
            if (data.features) {
                for (const f of data.features) {
                    allPOIs.push({
                        name: f.text || f.place_name.split(',')[0],
                        address: f.place_name,
                        lng: f.center[0],
                        lat: f.center[1],
                        icon: poiType.icon,
                        color: poiType.color,
                        label: poiType.label,
                    });
                }
            }
        } catch (e) {
            console.warn(`Failed to fetch ${poiType.label}:`, e);
        }
    }

    return allPOIs;
}


function MapView({ onLocationClick, route, heatmapVisible, safeLocationsVisible, onMapReady }) {
    const mapContainer = useRef(null);
    const mapRef = useRef(null);
    const markersRef = useRef([]);
    const [mapLoaded, setMapLoaded] = useState(false);

    // Initialize map
    useEffect(() => {
        if (!mapContainer.current) return;

        // Clean up any existing map
        if (mapRef.current) {
            mapRef.current.remove();
            mapRef.current = null;
        }

        mapboxgl.accessToken = MAPBOX_TOKEN;

        const map = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/dark-v11',
            center: STL_CENTER,
            zoom: STL_ZOOM,
            pitch: 0,
            bearing: 0,
            antialias: true,
        });

        map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

        map.on('load', () => {
            setMapLoaded(true);
            if (onMapReady) onMapReady(map);

            // Add heatmap tile source (starts hidden)
            map.addSource('heatmap-tiles', {
                type: 'raster',
                tiles: [`${API_URL}/tiles/{z}/{x}/{y}.png`],
                tileSize: 256,
            });

            map.addLayer({
                id: 'heatmap-layer',
                type: 'raster',
                source: 'heatmap-tiles',
                paint: {
                    'raster-opacity': 0,
                    'raster-opacity-transition': { duration: 500 },
                },
            });
        });

        // Click handler — use reverse geocoding for street names
        map.on('click', async (e) => {
            const { lng, lat } = e.lngLat;

            // First try to get name from map features (faster)
            const features = map.queryRenderedFeatures(e.point, {
                layers: ['road-label', 'poi-label', 'place-label'].filter(l => {
                    try { return map.getLayer(l); } catch { return false; }
                }),
            });

            let name = null;
            let type = 'pin';

            if (features.length > 0) {
                const f = features[0];
                name = f.properties.name || f.properties.name_en || null;
                type = f.layer.id.includes('road') ? 'road' : 'poi';
            }

            // Fallback: use Mapbox reverse geocoding for street name
            if (!name) {
                const geocodedName = await reverseGeocode(lat, lng);
                if (geocodedName) {
                    name = geocodedName;
                    type = 'road';
                } else {
                    name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                }
            }

            if (onLocationClick) {
                onLocationClick({ name, lat, lng, type });
            }
        });

        map.on('mouseenter', 'poi-label', () => {
            map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', 'poi-label', () => {
            map.getCanvas().style.cursor = '';
        });

        mapRef.current = map;

        return () => {
            map.remove();
            mapRef.current = null;
            setMapLoaded(false);
        };
    }, []);

    // Toggle heatmap visibility
    useEffect(() => {
        if (!mapRef.current || !mapLoaded) return;

        try {
            mapRef.current.setPaintProperty(
                'heatmap-layer',
                'raster-opacity',
                heatmapVisible ? 0.7 : 0
            );
        } catch (e) {
            // Layer might not exist yet
        }
    }, [heatmapVisible, mapLoaded]);

    // Render route
    useEffect(() => {
        if (!mapRef.current || !mapLoaded) return;
        const map = mapRef.current;

        // Remove existing route layers and markers
        if (map.getLayer('route-line')) map.removeLayer('route-line');
        if (map.getLayer('route-outline')) map.removeLayer('route-outline');
        if (map.getSource('route-source')) map.removeSource('route-source');

        // Remove route markers
        markersRef.current
            .filter(m => m._routeMarker)
            .forEach(m => m.remove());
        markersRef.current = markersRef.current.filter(m => !m._routeMarker);

        if (!route || !route.coordinates || route.coordinates.length === 0) return;

        map.addSource('route-source', {
            type: 'geojson',
            data: {
                type: 'Feature',
                properties: {},
                geometry: {
                    type: 'LineString',
                    coordinates: route.coordinates,
                },
            },
        });

        // Outer glow line
        map.addLayer({
            id: 'route-outline',
            type: 'line',
            source: 'route-source',
            layout: {
                'line-join': 'round',
                'line-cap': 'round',
            },
            paint: {
                'line-color': '#818cf8',
                'line-width': 9,
                'line-opacity': 0.3,
            },
        });

        // Inner line
        map.addLayer({
            id: 'route-line',
            type: 'line',
            source: 'route-source',
            layout: {
                'line-join': 'round',
                'line-cap': 'round',
            },
            paint: {
                'line-color': '#6366f1',
                'line-width': 5,
                'line-opacity': 0.95,
            },
        });

        // Start and end markers
        const startCoord = route.coordinates[0];
        const endCoord = route.coordinates[route.coordinates.length - 1];

        const createRouteMarker = (lngLat, label, color) => {
            const el = document.createElement('div');
            el.style.width = '24px';
            el.style.height = '24px';
            el.style.borderRadius = '50%';
            el.style.background = color;
            el.style.border = '3px solid white';
            el.style.boxShadow = `0 0 12px ${color}80`;
            const m = new mapboxgl.Marker({ element: el })
                .setLngLat(lngLat)
                .addTo(map);
            m._routeMarker = true;
            return m;
        };

        markersRef.current.push(createRouteMarker(startCoord, 'A', '#10b981'));
        markersRef.current.push(createRouteMarker(endCoord, 'B', '#ef4444'));

        // Fit bounds to route
        const bounds = new mapboxgl.LngLatBounds();
        route.coordinates.forEach(coord => bounds.extend(coord));
        map.fitBounds(bounds, { padding: 100, duration: 1000 });
    }, [route, mapLoaded]);

    // Safe locations — use REAL Mapbox Places API data
    useEffect(() => {
        // Clear existing safe markers
        markersRef.current
            .filter(m => m._safeMarker)
            .forEach(m => m.remove());
        markersRef.current = markersRef.current.filter(m => !m._safeMarker);

        if (!safeLocationsVisible || !mapRef.current) return;

        const center = mapRef.current.getCenter();

        fetchSafePOIs(center.lng, center.lat).then(pois => {
            for (const poi of pois) {
                const el = document.createElement('div');
                el.style.width = '30px';
                el.style.height = '30px';
                el.style.borderRadius = '50%';
                el.style.background = poi.color;
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.justifyContent = 'center';
                el.style.fontSize = '15px';
                el.style.boxShadow = `0 0 14px ${poi.color}60`;
                el.style.cursor = 'pointer';
                el.style.border = '2px solid rgba(255,255,255,0.4)';
                el.textContent = poi.icon;

                const popup = new mapboxgl.Popup({ offset: 20, closeButton: true })
                    .setHTML(`
            <div class="safe-popup-name">${poi.name}</div>
            <div class="safe-popup-type">${poi.label}</div>
            <div class="safe-popup-addr">${poi.address.split(',').slice(0, 2).join(',')}</div>
          `);

                const marker = new mapboxgl.Marker({ element: el })
                    .setLngLat([poi.lng, poi.lat])
                    .setPopup(popup)
                    .addTo(mapRef.current);

                marker._safeMarker = true;
                markersRef.current.push(marker);
            }
        });
    }, [safeLocationsVisible]);

    return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />;
}

export default MapView;
