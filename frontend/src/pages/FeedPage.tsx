/**
 * FeedPage — dedicated full-page feed view.
 * Owner: Person 4 (Frontend UI + Features)
 *
 * This is a separate page at /feed — wraps the LiveFeed component.
 */
import LiveFeed from '../components/LiveFeed';

export default function FeedPage() {
    // TODO: add filtering controls (by category, severity, radius)
    return (
        <div className="feed-page">
            <h2>Community Safety Feed</h2>
            <p className="feed-page-subtitle">
                Real-time safety reports from the St. Louis community
            </p>
            <LiveFeed />
        </div>
    );
}
