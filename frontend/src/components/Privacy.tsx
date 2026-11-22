import { Heading } from './shared/Heading';

const Privacy = () => {
    return (
        <div className="max-w-3xl mx-auto px-6 py-12 text-sm leading-relaxed">
            <Heading level="page" className="mb-2">Privacy Policy</Heading>
            <p className="text-(--text-tertiary) mb-8">Last updated: November 21, 2026</p>

            <section className="mb-8">
                <Heading level="section" className="mb-3">Overview</Heading>
                <p>
                    MLB Showdown Card Bot ("the app") is a fan-made tool for generating MLB Showdown
                    trading card stats. This policy describes what information we collect when you
                    use the app or sign in, how we use it, and how we protect it.
                </p>
            </section>

            <section className="mb-8">
                <Heading level="section" className="mb-3">1. Data Accessed</Heading>
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
                <Heading level="section" className="mb-3">2. Data Usage</Heading>
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
                <Heading level="section" className="mb-3">3. Usage Data</Heading>
                <p className="mb-3">
                    Whether or not you sign in, the app records how its features are used, so we can
                    see what's popular and find what's broken:
                </p>
                <ul className="list-disc list-inside space-y-1 mb-3">
                    <li>Pages you open, cards you build or look up, and searches you run</li>
                    <li>Errors you run into while building a card</li>
                    <li>
                        Where your visit came from (the referring site), your rough device type
                        (phone, tablet or desktop) and your screen width
                    </li>
                    <li>
                        A random ID stored in your browser, so repeat visits count as one visitor,
                        and a random ID for each browser tab session. If you sign in, this activity
                        is linked to your account
                    </li>
                </ul>
                <p className="mb-3">
                    This data stays in our own database. It is not sent to analytics or advertising
                    services, and it is only used to improve the app.
                </p>
                <p>
                    If your browser sends a Global Privacy Control or Do Not Track signal, the app
                    does not record page views or the random IDs. You can also clear the IDs at any
                    time by clearing this site's data in your browser.
                </p>
            </section>

            <section className="mb-8">
                <Heading level="section" className="mb-3">4. Data Sharing</Heading>
                <p className="mb-3">
                    We do <strong>not</strong> sell, rent, or trade your personal information.
                    Limited sharing occurs only as follows:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>
                        <strong>Supabase</strong> — our authentication and database provider, which
                        stores your account credentials, session tokens and usage data. Supabase
                        processes this data solely to provide these services.
                    </li>
                </ul>
                <p className="mt-3">
                    No account or usage data is sold or shared with analytics providers,
                    advertisers, or any other third parties.
                </p>
            </section>

            <section className="mb-8">
                <Heading level="section" className="mb-3">5. Data Storage & Protection</Heading>
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
                <Heading level="section" className="mb-3">6. Data Retention & Deletion</Heading>
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
                    Upon deletion, your email address, display name, any saved card data and the
                    usage data linked to your account will be permanently removed from our systems.
                </p>
            </section>

            <section className="mb-8">
                <Heading level="section" className="mb-3">Third-Party Privacy Policies</Heading>
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
                <Heading level="section" className="mb-3">Changes to This Policy</Heading>
                <p>
                    If this policy changes materially, we will update the "Last updated" date at
                    the top of this page.
                </p>
            </section>
        </div>
    );
};

export default Privacy;
