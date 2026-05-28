const Privacy = () => {
    return (
        <div className="max-w-3xl mx-auto px-6 py-12 text-sm leading-relaxed">
            <h1 className="text-2xl font-bold mb-2">Privacy Policy</h1>
            <p className="text-gray-500 mb-8">Last updated: May 27, 2026</p>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">Overview</h2>
                <p>
                    MLB Showdown Card Bot ("the app") is a fan-made tool for generating MLB Showdown
                    trading card stats. This policy describes what information we collect when you
                    sign in, how we use it, and how we protect it.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">1. Data Accessed</h2>
                <p className="mb-3">
                    When you sign in using a third-party provider (such as Google), the app
                    requests only the minimum information needed to create and identify your
                    account:
                </p>
                <ul className="list-disc list-inside space-y-1 mb-3">
                    <li>
                        <strong>Email address</strong> — to uniquely identify your account
                    </li>
                    <li>
                        <strong>Basic profile information</strong> (name, profile picture) — to
                        personalize your account display
                    </li>
                </ul>
                <p>
                    We do <strong>not</strong> access email inboxes, cloud storage, contacts,
                    calendars, or any other service data beyond the basic sign-in profile
                    described above.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">2. Data Usage</h2>
                <p className="mb-3">
                    Information received from sign-in providers is used exclusively to:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>Authenticate you and maintain your session in the app</li>
                    <li>Associate saved card configurations or preferences with your account</li>
                    <li>Display your name or profile picture within the app interface</li>
                </ul>
                <p className="mt-3">
                    This data is never used for advertising, profiling, or any purpose unrelated
                    to providing app functionality.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">3. Data Sharing</h2>
                <p className="mb-3">
                    We do <strong>not</strong> sell, rent, or trade your personal information.
                    Limited sharing occurs only as follows:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>
                        <strong>Supabase</strong> — our authentication and database provider, which
                        stores your account credentials and session tokens. Supabase processes this
                        data solely to provide these services.
                    </li>
                </ul>
                <p className="mt-3">
                    No account data is shared with analytics providers, advertisers, or any other
                    third parties.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">4. Data Storage & Protection</h2>
                <p className="mb-3">
                    Account data (email, display name) is stored in Supabase's managed PostgreSQL
                    database, which provides:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>Encryption at rest and in transit (TLS)</li>
                    <li>Access controls limiting data access to authenticated application code</li>
                    <li>
                        OAuth tokens managed by Supabase Auth — we never store raw provider tokens
                        directly
                    </li>
                </ul>
                <p className="mt-3">
                    The app is accessed over HTTPS. OAuth session state is managed by Supabase
                    Auth within a secure session cookie and is not persisted in client-side storage.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">5. Data Retention & Deletion</h2>
                <p className="mb-3">
                    Your account information is retained for as long as your account remains
                    active. If you stop using the app, data is not automatically deleted, but you
                    may request deletion at any time.
                </p>
                <p className="mb-3">
                    <strong>To request deletion of your account and all associated data</strong>,
                    please open an issue on the project's GitHub repository and include the email
                    address associated with your account. We will complete the deletion within 30
                    days.
                </p>
                <p>
                    Upon deletion, your email address, display name, and any saved card data
                    associated with your account will be permanently removed from our systems.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">Third-Party Privacy Policies</h2>
                <p className="mb-3">
                    Your use of a third-party sign-in provider is also governed by that provider's
                    own privacy policy. For reference:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>
                        <a
                            href="https://policies.google.com/privacy"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline"
                        >
                            Google Privacy Policy
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://supabase.com/privacy"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline"
                        >
                            Supabase Privacy Policy
                        </a>
                    </li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-lg font-semibold mb-3">Changes to This Policy</h2>
                <p>
                    If this policy changes materially, we will update the "Last updated" date at
                    the top of this page.
                </p>
            </section>
        </div>
    );
};

export default Privacy;
