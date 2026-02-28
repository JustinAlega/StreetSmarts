/**
 * Header — app name + navigation.
 * Owner: Person 4 (Frontend UI + Features)
 *
 * Purely visual — no API calls.
 */
import { Link } from 'react-router-dom';

export default function Header() {
    // TODO: add branding, logo, and polished nav styles
    return (
        <header className="app-header">
            <Link to="/" className="logo">
                🛡️ <span>StreetSense</span> <span className="logo-accent">STL</span>
            </Link>
            <nav>
                <Link to="/">Map</Link>
                <Link to="/feed">Feed</Link>
            </nav>
        </header>
    );
}
