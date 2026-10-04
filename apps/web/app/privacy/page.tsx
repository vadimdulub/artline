import { pageMetadata } from "@/lib/seo";

export function generateMetadata() {
  return pageMetadata("Privacy", "How Artline uses account information, sign-in cookies and technical service data, and how to contact its operator.", "/privacy");
}

export default function PrivacyPage() {
  return <main id="main-content" className="admin-page prose-page">
    <h1>Privacy</h1>
    <p>Last updated: 28 September 2026.</p>
    <p>Artline is operated by Vadim Dulub. For privacy questions or requests about your information, contact <a href="mailto:vadim@alingva.com">vadim@alingva.com</a>.</p>

    <h2>Browsing and Google sign-in</h2>
    <p>You can browse the public atlas without an account. If you choose Google sign-in when it is available, Google shares an account identifier, your name and your email address with Artline. We use these details to create and recognize your Artline account and display your account information. Google also confirms whether your email address is verified.</p>
    <p>Artline requests basic identity information only. It does not request access to your Gmail messages, Drive files, contacts or calendar. Your Google password stays with Google. Artline does not store Google access or refresh tokens.</p>

    <h2>Cookies and account records</h2>
    <p>Sign-in uses a short-lived cookie to complete the login process and a session cookie to keep you signed in for up to 30 days. Blocking these cookies prevents sign-in from working. Signing out ends that session; it does not delete your account.</p>
    <p>Account records include your Google account identifier, name, email address and account creation and update times. Session records contain a protected token reference and creation and expiry times. Expired sessions cannot be used to sign in, even if their records have not yet been removed.</p>

    <h2>Hosting and service information</h2>
    <p>Artline runs on Google Cloud, and Cloudflare provides its domain and DNS services. Hosting services may process technical information such as IP addresses, browser details, request times and errors to deliver, secure and troubleshoot the site. Artline uses account information to provide and protect your account, not for advertising, and does not sell Google account data.</p>
    <p>Google handles its own sign-in service under <a href="https://policies.google.com/privacy">Google’s privacy policy</a>. If you follow a link to a museum, archive or another website, that site has its own privacy practices.</p>

    <h2>Keeping and deleting information</h2>
    <p>Your account information remains stored while your Artline account exists. You can ask to access, correct or delete it by emailing <a href="mailto:vadim@alingva.com">vadim@alingva.com</a>. We may need to verify that the request concerns your account. There is currently no automatic account-deletion button.</p>
    <p>Security logs and backup copies are kept separately from the live account. Removing a live account does not immediately remove every backup copy. Revoking Artline’s access in your Google Account also does not automatically delete the existing Artline account; contact us to request that deletion.</p>

    <h2>Changes</h2>
    <p>This page describes the current account service. We will update it when the way Artline handles personal information changes. The date above identifies the latest version.</p>
  </main>;
}
