/**
 * LiveFeed — list of community posts + submit form.
 * Owner: Person 4 (Frontend UI + Features)
 *
 * Standalone component — doesn't depend on MapView or RoutePanel.
 */
import { useEffect, useState } from 'react';

interface Post {
    id: string;
    lat: number;
    long: number;
    severity: number;
    category: string;
    content: string;
    created_at: string;
}

interface LiveFeedProps {
    /** Center coords to fetch nearby posts. Defaults to STL center. */
    lat?: number;
    lng?: number;
}

export default function LiveFeed({ lat = 38.627, lng = -90.199 }: LiveFeedProps) {
    const [posts, setPosts] = useState<Post[]>([]);
    const [newContent, setNewContent] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        // TODO:
        // 1. GET /api/feed?lat=...&lng=...&radius=500
        // 2. setPosts(response)
        async function fetchFeed() {
            // STUB
            console.log('Fetching feed near:', lat, lng);
        }
        fetchFeed();
    }, [lat, lng]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!newContent.trim()) return;

        // TODO:
        // 1. POST /api/post { lat, lng, content: newContent }
        // 2. Prepend new post to posts list
        // 3. Clear input
        setSubmitting(true);
        try {
            // STUB
            console.log('Submitting post:', newContent);
            setNewContent('');
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="live-feed">
            <h3>📢 Live Feed</h3>

            <form onSubmit={handleSubmit} className="feed-form">
                <textarea
                    placeholder="Report a safety concern…"
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    rows={3}
                />
                <button type="submit" disabled={submitting}>
                    {submitting ? 'Posting…' : 'Submit Report'}
                </button>
            </form>

            <ul className="feed-list">
                {posts.length === 0 && <li className="placeholder">No reports yet.</li>}
                {posts.map((post) => (
                    <li key={post.id} className="feed-item">
                        {/* TODO: render severity badge, category tag, timestamp, content */}
                        <span className="category-tag">{post.category}</span>
                        <p>{post.content}</p>
                        <time>{post.created_at}</time>
                    </li>
                ))}
            </ul>
        </div>
    );
}
