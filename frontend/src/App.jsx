import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import SummaryPanel from './components/SummaryPanel';
import MapHeader from './components/MapHeader';
import MapLegend from './components/MapLegend';
import LocationFeedPage from './pages/LocationFeedPage';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function MapPage() {
  const [route, setRoute] = useState(null);
  const [location, setLocation] = useState(null);
  const [heatmapVisible, setHeatmapVisible] = useState(false);
  const [safeLocationsVisible, setSafeLocationsVisible] = useState(false);
  const [safeLoading, setSafeLoading] = useState(false);
  const [mapRef, setMapRef] = useState(null);

  const handleLocationClick = (loc) => {
    setLocation(loc);
  };

  const handleRouteComputed = (routeData) => {
    setRoute(routeData);
  };

  const handleToggleHeatmap = () => {
    setHeatmapVisible(!heatmapVisible);
  };

  const handleToggleSafe = () => {
    if (!safeLoading) setSafeLocationsVisible(!safeLocationsVisible);
  };

  const handleResetRoute = () => {
    setRoute(null);
  };

  const handleCloseSummary = () => {
    setLocation(null);
  };

  return (
    <div className="map-container">
      <MapHeader
        heatmapActive={heatmapVisible}
        safeActive={safeLocationsVisible}
        safeLoading={safeLoading}
        onToggleHeatmap={handleToggleHeatmap}
        onToggleSafe={handleToggleSafe}
        onResetRoute={handleResetRoute}
      />

      <MapView
        onLocationClick={handleLocationClick}
        route={route}
        heatmapVisible={heatmapVisible}
        safeLocationsVisible={safeLocationsVisible}
        onSafeLoadingChange={setSafeLoading}
        onMapReady={setMapRef}
      />

      <RoutePanel onRouteComputed={handleRouteComputed} />

      {location && (
        <SummaryPanel
          location={location}
          onClose={handleCloseSummary}
        />
      )}

      {heatmapVisible && <MapLegend />}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MapPage />} />
        <Route path="/location/:id" element={<LocationFeedPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
