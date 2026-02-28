/**
 * App — top-level router.
 * Owner: Person 3 (Frontend Map + Routing) sets up router.
 *        Person 4 (Frontend UI) adds routes for feed page.
 *
 * MERGE NOTE: Person 3 owns the "/" route, Person 4 owns "/feed".
 *             Add new routes at the bottom of the <Routes> block.
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import SummaryPanel from './components/SummaryPanel';
import LiveFeed from './components/LiveFeed';
import MapLegend from './components/MapLegend';
import FeedPage from './pages/FeedPage';

function App() {
    return (
        <BrowserRouter>
            <Header />
            <Routes>
                {/* Person 3: Main map view */}
                <Route
                    path="/"
                    element={
                        <main className="app-layout">
                            <div className="map-container">
                                <MapView />
                                <MapLegend />
                            </div>
                            <aside className="sidebar">
                                <RoutePanel />
                                <SummaryPanel />
                            </aside>
                        </main>
                    }
                />

                {/* Person 4: Dedicated feed page */}
                <Route path="/feed" element={<FeedPage />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
