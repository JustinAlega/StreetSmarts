import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Saint Louis center
const STL_CENTER = [-90.1994, 38.6270];
const STL_ZOOM = 12.5;

const SAFE_ICON_MAP = {
    hospital: '<svg viewBox="0 0 24 24" fill="white" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M8.25 5.25H15.75V11.25V20.25H14.25V13.5H9.75V20.25H8.25V14.25V5.25ZM11.25 20.25H12.75V15H11.25V20.25ZM15.75 21.75H8.25H6.75H2.25V14.25H6.75V3.75H17.25V11.25H21.75V21.75H17.25H15.75ZM6.75 15.75V20.25H3.75V15.75H6.75ZM17.25 20.25H20.25V12.75H17.25V20.25ZM11.25 7.5V8.25H10.5V9.75H11.25V10.5H12.75V9.75H13.5V8.25H12.75V7.5H11.25Z"/></svg>',
    police: '<svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M4 21V19.5C4 16.4624 6.46243 14 9.5 14H14.5C17.5376 14 20 16.4624 20 19.5V21M8 21V18.5M16 21V18.3333M8.5 6.5C10.514 8.22631 13.486 8.22631 15.5 6.5M16 7V4.92755L17.4657 2.78205C17.6925 2.45018 17.4548 2 17.0529 2H6.94712C6.5452 2 6.30755 2.45018 6.53427 2.78205L8 4.92755V7M16 8C16 10.2091 14.2091 12 12 12C9.79086 12 8 10.2091 8 8V5.5H16V8Z" stroke="white" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.4"/></svg>',
    fire_station: '<svg viewBox="0 0 50 50" fill="white" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M36.90625 3C36.796875 3.015625 36.691406 3.046875 36.59375 3.09375L1.90625 18.5C1.609375 18.621094 1.390625 18.875 1.3125 19.1875L0.03125 24.78125C-0.046875 25.148438 0.0859375 25.527344 0.375 25.761719C0.664063 26 1.0625 26.054688 1.40625 25.90625L6 23.875L6 28L3 28C1.355469 28 0 29.355469 0 31L0 39C0 40.644531 1.355469 42 3 42L7.09375 42C7.570313 44.835938 10.035156 47 13 47C15.964844 47 18.429688 44.835938 18.90625 42L33.09375 42C33.570313 44.835938 36.035156 47 39 47C41.964844 47 44.429688 44.835938 44.90625 42L47 42C48.644531 42 50 40.644531 50 39L50 30.09375C50 29.460938 49.882813 28.960938 49.78125 28.5625L49.75 28.5L49.75 28.46875L46.9375 20.375L46.9375 20.34375C46.199219 18.371094 44.320313 17 42.1875 17L25 17C23.355469 17 22 18.355469 22 20L22 28L14 28L14 20.3125L42.40625 7.71875C42.75 7.566406 42.980469 7.234375 43 6.855469C43.019531 6.480469 42.828125 6.125 42.5 5.9375L37.5 3.125C37.320313 3.023438 37.113281 2.980469 36.90625 3ZM37.0625 5.1875L39.75 6.6875L35.78125 8.4375ZM35.8125 5.625L34.46875 9.03125L33.90625 9.28125L30.5625 7.96875ZM29.3125 8.5L32.625 9.84375L27.34375 12.1875L28.6875 8.78125ZM27.40625 9.34375L26.09375 12.75L25.53125 13L22.125 11.6875ZM20.84375 12.28125L24.25 13.59375L18.9375 15.9375L20.3125 12.5ZM19.0625 13.0625L17.6875 16.5L17.15625 16.71875L13.75 15.4375ZM12.4375 16L15.875 17.3125L10.5625 19.6875L11.84375 16.28125ZM10.53125 16.84375L9.28125 20.25L8.71875 20.5L5.3125 19.15625ZM25 19L42.1875 19C43.4375 19 44.589844 19.800781 45.0625 21L40 21C39.476563 21 38.941406 21.183594 38.5625 21.5625C38.183594 21.941406 38 22.476563 38 23L38 28C38 28.523438 38.183594 29.058594 38.5625 29.4375C38.941406 29.816406 39.476563 30 40 30L48 30C48 30.03125 48 30.058594 48 30.09375L48 39C48 39.554688 47.554688 40 47 40L44.90625 40C44.429688 37.164063 41.964844 35 39 35C36.035156 35 33.570313 37.164063 33.09375 40L18.90625 40C18.429688 37.164063 15.964844 35 13 35C10.035156 35 7.570313 37.164063 7.09375 40L3 40C2.445313 40 2 39.554688 2 39L2 31C2 30.445313 2.445313 30 3 30L24 30L24 20C24 19.445313 24.445313 19 25 19ZM4.03125 19.71875L7.4375 21.0625L6.90625 21.28125C6.894531 21.28125 6.886719 21.28125 6.875 21.28125C6.636719 21.308594 6.414063 21.417969 6.25 21.59375L2.4375 23.28125L3.15625 20.125ZM28 21C27.476563 21 26.941406 21.183594 26.5625 21.5625C26.183594 21.941406 26 22.476563 26 23L26 28C26 28.523438 26.183594 29.058594 26.5625 29.4375C26.941406 29.816406 27.476563 30 28 30L34 30C34.523438 30 35.058594 29.816406 35.4375 29.4375C35.816406 29.058594 36 28.523438 36 28L36 23C36 22.476563 35.816406 21.941406 35.4375 21.5625C35.058594 21.183594 34.523438 21 34 21ZM12 21.21875L12 28L8 28L8 22.96875ZM28 23L34 23L34 28L28 28ZM40 23L45.71875 23L47.46875 28L40 28ZM13 37C15.222656 37 17 38.777344 17 41C17 43.222656 15.222656 45 13 45C10.777344 45 9 43.222656 9 41C9 38.777344 10.777344 37 13 37ZM39 37C41.222656 37 43 38.777344 43 41C43 43.222656 41.222656 45 39 45C36.777344 45 35 43.222656 35 41C35 38.777344 36.777344 37 39 37Z"/></svg>',
    pharmacy: '<svg viewBox="0 0 256 256" fill="white" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M190.23926,82.92725a7.99946,7.99946,0,0,1-.19629,11.312l-24.416,23.584a7.99966,7.99966,0,1,1-11.11523-11.50781l24.416-23.584A7.99843,7.99843,0,0,1,190.23926,82.92725Zm23.418,34.72949-96,96a53.255,53.255,0,0,1-75.31446-75.31348l96-96a53.255,53.255,0,0,1,75.31446,75.31348Zm-11.31446-64a37.25409,37.25409,0,0,0-52.68554,0L107.31348,96,160,148.68628l42.34277-42.343A37.2969,37.2969,0,0,0,202.34277,53.65674Z"/></svg>',
    library: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="1.91" stroke-miterlimit="10" xmlns="http://www.w3.org/2000/svg"><rect x="7.23" y="5.32" width="9.55" height="3.82"/><path d="M20.59,22.5H5.32A1.91,1.91,0,0,1,4,19.24a1.89,1.89,0,0,1,1.35-.56H20.59"/><line x1="19.64" y1="18.68" x2="19.64" y2="22.5"/><path d="M20.59,1.5V18.68H5.32a1.91,1.91,0,0,0-1.91,1.91V3.41A1.92,1.92,0,0,1,5.32,1.5Z"/></svg>',
    gas_station: '<svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M3.5 22V5C3.5 3 4.84 2 6.5 2H14.5C16.16 2 17.5 3 17.5 5V22H3.5Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 22H19" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.39 9.99998H12.62C13.66 9.99998 14.51 9.49999 14.51 8.10999V6.87999C14.51 5.48999 13.66 4.98999 12.62 4.98999H8.39C7.35 4.98999 6.5 5.48999 6.5 6.87999V8.10999C6.5 9.49999 7.35 9.99998 8.39 9.99998Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 13H9.5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M17.5 16.01L22 16V10L20 9" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    urgent_care: '<svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M17 12C19.7614 12 22 9.76142 22 7C22 4.23858 19.7614 2 17 2C14.2386 2 12 4.23858 12 7C12 7.79984 12.1878 8.55582 12.5217 9.22624C12.6105 9.4044 12.64 9.60803 12.5886 9.80031L12.2908 10.9133C12.1615 11.3965 12.6035 11.8385 13.0867 11.7092L14.1997 11.4114C14.392 11.36 14.5956 11.3895 14.7738 11.4783C15.4442 11.8122 16.2002 12 17 12Z" stroke="white" stroke-width="1.5"/><path d="M17 9L17 5M19 7L15 7" stroke="white" stroke-width="1.5" stroke-linecap="round"/><path d="M14.1008 16.0272L14.6446 16.5437L14.1008 16.0272ZM14.5562 15.5477L14.0124 15.0312L14.5562 15.5477ZM16.9729 15.2123L16.5987 15.8623L16.9729 15.2123ZM18.8834 16.312L18.5092 16.962L18.8834 16.312ZM19.4217 19.7584L19.9655 20.275L19.4217 19.7584ZM18.0012 21.254L17.4574 20.7375L18.0012 21.254ZM16.6763 21.9631L16.75 22.7095L16.6763 21.9631ZM6.8154 17.4752L7.3592 16.9587L6.8154 17.4752ZM2.75185 7.92574C2.72965 7.51212 2.37635 7.19481 1.96273 7.21701C1.54911 7.23921 1.23181 7.59252 1.25401 8.00613L2.75185 7.92574ZM8.19075 9.80507L8.73454 10.3216L8.19075 9.80507ZM8.47756 9.50311L9.02135 10.0196L8.47756 9.50311ZM8.63428 6.6931L9.24668 6.26012L8.63428 6.6931ZM7.3733 4.90961L6.7609 5.3426L7.3733 4.90961ZM3.7177 4.09213C3.43244 4.39246 3.44465 4.86717 3.74498 5.15244C4.04531 5.4377 4.52002 5.42549 4.80529 5.12516L3.7177 4.09213ZM10.0632 14.0559L10.607 13.5394L10.0632 14.0559ZM9.6641 20.8123C10.0148 21.0327 10.4778 20.9271 10.6982 20.5764C10.9186 20.2257 10.8129 19.7627 10.4622 19.5423L9.6641 20.8123ZM14.113 21.0584C13.7076 20.9735 13.3101 21.2334 13.2252 21.6388C13.1403 22.0442 13.4001 22.4417 13.8056 22.5266L14.113 21.0584ZM14.6446 16.5437L15.1 16.0642L14.0124 15.0312L13.557 15.5107L14.6446 16.5437ZM16.5987 15.8623L18.5092 16.962L19.2575 15.662L17.347 14.5623L16.5987 15.8623ZM18.8779 19.2419L17.4574 20.7375L18.545 21.7705L19.9655 20.275L18.8779 19.2419ZM7.3592 16.9587C3.48307 12.8778 2.83289 9.43556 2.75185 7.92574L1.25401 8.00613C1.35326 9.85536 2.13844 13.6403 6.27161 17.9917L7.3592 16.9587ZM8.73454 10.3216L9.02135 10.0196L7.93377 8.9866L7.64695 9.28856L8.73454 10.3216ZM9.24668 6.26012L7.98569 4.47663L6.7609 5.3426L8.02189 7.12608L9.24668 6.26012ZM9.51937 14.5724C11.0422 16.1757 12.1924 16.806 13.0699 16.9485C13.5201 17.0216 13.8846 16.9632 14.1606 16.8544C14.2955 16.8012 14.4023 16.7387 14.4824 16.6819C14.5223 16.6535 14.5556 16.6266 14.5825 16.6031C14.5959 16.5913 14.6078 16.5803 14.6181 16.5703C14.6233 16.5654 14.628 16.5606 14.6324 16.5562C14.6346 16.554 14.6368 16.5518 14.6388 16.5497C14.6398 16.5487 14.6408 16.5477 14.6417 16.5467C14.6422 16.5462 14.6429 16.5454 14.6432 16.5452C14.6439 16.5444 14.6446 16.5437 14.1008 16.0272C13.557 15.5107 13.5577 15.51 13.5583 15.5093C13.5586 15.509 13.5592 15.5083 13.5597 15.5078C13.5606 15.5069 13.5615 15.506 13.5623 15.5051C13.5641 15.5033 13.5658 15.5015 13.5675 15.4998C13.5708 15.4965 13.574 15.4933 13.577 15.4904C13.5831 15.4846 13.5885 15.4796 13.5933 15.4754C13.6029 15.467 13.61 15.4616 13.6146 15.4584C13.6239 15.4517 13.623 15.454 13.6102 15.459C13.5909 15.4666 13.5001 15.4987 13.3103 15.4679C12.9078 15.4025 12.0391 15.0472 10.607 13.5394L9.51937 14.5724ZM7.98569 4.47663C6.9721 3.04305 4.94388 2.80119 3.7177 4.09213L4.80529 5.12516C5.32812 4.57471 6.24855 4.61795 6.7609 5.3426L7.98569 4.47663ZM17.4574 20.7375C17.1783 21.0313 16.8864 21.1887 16.6026 21.2167L16.75 22.7095C17.497 22.6357 18.1016 22.2373 18.545 21.7705L17.4574 20.7375ZM9.02135 10.0196C9.98893 9.00095 10.0574 7.40678 9.24668 6.26012L8.02189 7.12608C8.44404 7.72315 8.3793 8.51753 7.93377 8.9866L9.02135 10.0196ZM18.5092 16.962C19.3301 17.4345 19.4907 18.5968 18.8779 19.2419L19.9655 20.2749C21.2705 18.901 20.8904 16.6019 19.2575 15.662L18.5092 16.962ZM15.1 16.0642C15.4854 15.6584 16.086 15.5672 16.5987 15.8623L17.347 14.5623C16.2485 13.93 14.8862 14.1113 14.0124 15.0312L15.1 16.0642ZM10.4622 19.5423C9.47846 18.9241 8.43149 18.0876 7.3592 16.9587L6.27161 17.9917C7.42564 19.2067 8.56897 20.1241 9.6641 20.8123L10.4622 19.5423ZM16.6026 21.2167C16.0561 21.2707 15.1912 21.2842 14.113 21.0584L13.8056 22.5266C15.0541 22.788 16.0742 22.7762 16.75 22.7095L16.6026 21.2167Z" fill="white"/><path d="M8.19075 9.80507C7.64695 9.28856 7.64626 9.28929 7.64556 9.29002C7.64533 9.29028 7.64463 9.29102 7.64415 9.29152C7.6432 9.29254 7.64223 9.29357 7.64125 9.29463C7.63928 9.29675 7.63724 9.29896 7.63515 9.30127C7.63095 9.30588 7.6265 9.31087 7.62182 9.31625C7.61247 9.32701 7.60219 9.33931 7.5912 9.3532C7.56922 9.38098 7.54435 9.41511 7.51826 9.45588C7.46595 9.53764 7.40921 9.64531 7.36117 9.78033C7.26346 10.0549 7.21022 10.4185 7.27675 10.8726C7.40746 11.7647 7.99202 12.9644 9.51937 14.5724L10.607 13.5394C9.1793 12.0363 8.82765 11.1106 8.7609 10.6551C8.72871 10.4354 8.76142 10.3196 8.77436 10.2832C8.78163 10.2628 8.78639 10.2571 8.78174 10.2644C8.77948 10.2679 8.77498 10.2745 8.76742 10.2841C8.76363 10.2888 8.75908 10.2944 8.75364 10.3006C8.75092 10.3038 8.74798 10.3071 8.7448 10.3106C8.74321 10.3123 8.74156 10.3141 8.73985 10.3159C8.739 10.3169 8.73813 10.3178 8.73724 10.3187C8.7368 10.3192 8.73612 10.3199 8.7359 10.3202C8.73522 10.3209 8.73454 10.3216 8.19075 9.80507Z" fill="white"/></svg>',
};

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
 * Fetch nearby safe places from backend (Google Places API with live open/closed status).
 */
async function fetchSafePOIs(centerLng, centerLat) {
    try {
        const res = await fetch(
            `${API_URL}/nearby-safe?lat=${centerLat}&lng=${centerLng}&radius=3000`
        );
        const data = await res.json();
        if (data.error) {
            console.warn('[SafePlaces] Backend error:', data.error);
            return [];
        }
        return (data.places || []).map(p => ({
            ...p,
            icon: SAFE_ICON_MAP[p.type] || '🛡️',
        }));
    } catch (e) {
        console.warn('Failed to fetch safe places:', e);
        return [];
    }
}


function MapView({ onLocationClick, route, heatmapVisible, safeLocationsVisible, onSafeLoadingChange, onMapReady }) {
    const mapContainer = useRef(null);
    const mapRef = useRef(null);
    const markersRef = useRef([]);
    const safePOIsCache = useRef({ pois: null });
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
            style: 'mapbox://styles/mapbox/light-v11',
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
                'line-color': '#007BFC',
                'line-width': 5,
                'line-opacity': 0.95,
            },
        });

        // Start and end markers
        const startCoord = route.coordinates[0];
        const endCoord = route.coordinates[route.coordinates.length - 1];

        const createRouteMarker = (lngLat, label, color) => {
            const el = document.createElement('div');
            el.style.width = '32px';
            el.style.height = '32px';
            el.style.filter = 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))';
            el.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="32" height="32">
                <path fill-rule="evenodd" d="m11.54 22.351.07.04.028.016a.76.76 0 0 0 .723 0l.028-.015.071-.041a16.975 16.975 0 0 0 1.144-.742 19.58 19.58 0 0 0 2.683-2.282c1.944-1.99 3.963-4.98 3.963-8.827a8.25 8.25 0 0 0-16.5 0c0 3.846 2.02 6.837 3.963 8.827a19.58 19.58 0 0 0 2.682 2.282 16.975 16.975 0 0 0 1.145.742ZM12 13.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" clip-rule="evenodd" />
            </svg>`;
            const m = new mapboxgl.Marker({ element: el, anchor: 'bottom' })
                .setLngLat(lngLat)
                .addTo(map);
            m._routeMarker = true;
            return m;
        };

        markersRef.current.push(createRouteMarker(startCoord, 'A', '#000000'));
        markersRef.current.push(createRouteMarker(endCoord, 'B', '#000000'));

        // Fit bounds to route
        const bounds = new mapboxgl.LngLatBounds();
        route.coordinates.forEach(coord => bounds.extend(coord));
        map.fitBounds(bounds, { padding: 100, duration: 1000 });
    }, [route, mapLoaded]);

    // Render safe place markers on the map from POI data
    const renderSafeMarkers = (pois) => {
        for (const poi of pois) {
            const el = document.createElement('div');
            el.style.width = '32px';
            el.style.height = '32px';
            el.style.borderRadius = '50%';
            el.style.background = poi.color;
            el.style.display = 'flex';
            el.style.alignItems = 'center';
            el.style.justifyContent = 'center';
            el.style.fontSize = '15px';
            el.style.cursor = 'pointer';
            el.style.border = poi.open_now === false
                ? '2px solid rgba(255,255,255,0.15)'
                : '2px solid rgba(255,255,255,0.5)';
            el.style.boxShadow = poi.open_now === false
                ? `0 0 8px ${poi.color}30`
                : `0 0 14px ${poi.color}60`;
            el.style.opacity = poi.open_now === false ? '0.55' : '1';
            if (poi.icon.startsWith('<')) {
                el.innerHTML = poi.icon;
            } else {
                el.textContent = poi.icon;
            }

            const statusBadge = poi.open_now === true
                ? '<span class="safe-popup-badge open">Open Now</span>'
                : poi.open_now === false
                    ? '<span class="safe-popup-badge closed">Closed</span>'
                    : '<span class="safe-popup-badge unknown">Hours N/A</span>';

            const hoursHtml = poi.hours && poi.hours.length
                ? `<div class="safe-popup-hours">${poi.hours.join('<br>')}</div>`
                : '';

            const popup = new mapboxgl.Popup({ offset: 20, closeButton: true, maxWidth: '260px' })
                .setHTML(`
                    <div class="safe-popup-name">${poi.name}</div>
                    <div class="safe-popup-meta">
                        <span class="safe-popup-type">${poi.label}</span>
                        ${statusBadge}
                    </div>
                    <div class="safe-popup-addr">${poi.address}</div>
                    ${hoursHtml}
                `);

            const marker = new mapboxgl.Marker({ element: el })
                .setLngLat([poi.lng, poi.lat])
                .setPopup(popup)
                .addTo(mapRef.current);

            marker._safeMarker = true;
            markersRef.current.push(marker);
        }
    };

    // Safe locations — served from backend DB cache (refreshed weekly)
    useEffect(() => {
        // Clear existing safe markers
        markersRef.current
            .filter(m => m._safeMarker)
            .forEach(m => m.remove());
        markersRef.current = markersRef.current.filter(m => !m._safeMarker);

        if (!safeLocationsVisible || !mapRef.current) {
            if (onSafeLoadingChange) onSafeLoadingChange(false);
            return;
        }

        // Use session cache if available (avoid re-fetching on toggle)
        if (safePOIsCache.current.pois) {
            renderSafeMarkers(safePOIsCache.current.pois);
            if (onSafeLoadingChange) onSafeLoadingChange(false);
            return;
        }

        const center = mapRef.current.getCenter();

        // Signal loading start
        if (onSafeLoadingChange) onSafeLoadingChange(true);

        fetchSafePOIs(center.lng, center.lat).then(pois => {
            // Store in session cache
            safePOIsCache.current = { pois };
            renderSafeMarkers(pois);
        }).finally(() => {
            // Signal loading complete
            if (onSafeLoadingChange) onSafeLoadingChange(false);
        });
    }, [safeLocationsVisible]);

    return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />;
}

export default MapView;
