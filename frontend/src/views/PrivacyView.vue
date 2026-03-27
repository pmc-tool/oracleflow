<template>
  <div class="legal-page">
    <div class="legal-container">
      <h1 class="legal-title">Privacy Policy</h1>
      <p class="legal-updated">Last updated: March 26, 2026</p>

      <section class="legal-section">
        <h2>1. Introduction</h2>
        <p>
          OracleFlow ("we", "us", "our") is committed to protecting your privacy. This Privacy Policy
          explains how we collect, use, disclose, and safeguard your information when you use our
          geopolitical intelligence platform.
        </p>
      </section>

      <section class="legal-section">
        <h2>2. Information We Collect</h2>
        <p>We collect the following types of information:</p>
        <ul>
          <li><strong>Account Information:</strong> Email address, name, and password hash when you register</li>
          <li><strong>Usage Data:</strong> Pages visited, features used, session duration, and interaction patterns</li>
          <li><strong>Monitored Content:</strong> Web content scraped from sites you add to your monitoring list</li>
          <li><strong>Simulation Data:</strong> Inputs, parameters, and results from simulations you run</li>
          <li><strong>Device Information:</strong> Browser type, operating system, IP address, and device identifiers</li>
          <li><strong>Payment Information:</strong> Billing details processed securely through Stripe (we do not store card numbers)</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>3. How We Use Your Information</h2>
        <p>We use the information we collect to:</p>
        <ul>
          <li>Provide, maintain, and improve the Service</li>
          <li>Process your transactions and manage your account</li>
          <li>Generate intelligence signals and reports based on your monitored sites</li>
          <li>Run simulations and produce analytical results</li>
          <li>Send important service updates and security alerts</li>
          <li>Analyze usage patterns to improve product features</li>
          <li>Comply with legal obligations</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>4. Data Retention</h2>
        <p>
          We retain your personal data for as long as your account is active or as needed to provide the
          Service. Monitored site data is retained for 90 days by default and can be configured in your
          account settings. Upon account deletion, all personal data is permanently removed within 30 days.
          Anonymized, aggregated data may be retained indefinitely for analytical purposes.
        </p>
      </section>

      <section class="legal-section">
        <h2>5. Third-Party Services</h2>
        <p>We use the following third-party services that may process your data:</p>
        <ul>
          <li><strong>Stripe:</strong> Payment processing. Subject to <a href="https://stripe.com/privacy" class="legal-link" target="_blank" rel="noopener">Stripe's Privacy Policy</a></li>
          <li><strong>OpenAI:</strong> AI-powered analysis and natural language processing of intelligence data. Subject to <a href="https://openai.com/privacy" class="legal-link" target="_blank" rel="noopener">OpenAI's Privacy Policy</a></li>
          <li><strong>Novita AI:</strong> Supplementary AI model inference. Subject to Novita's Privacy Policy</li>
        </ul>
        <p>
          We ensure all third-party providers maintain appropriate data protection standards. We do not sell
          your personal data to any third party.
        </p>
      </section>

      <section class="legal-section">
        <h2>6. Data Security</h2>
        <p>
          We implement industry-standard security measures including encryption in transit (TLS), encryption
          at rest, secure password hashing, and regular security audits. However, no method of transmission
          over the Internet is 100% secure, and we cannot guarantee absolute security.
        </p>
      </section>

      <section class="legal-section">
        <h2>7. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
          <li><strong>Access:</strong> Request a copy of all personal data we hold about you</li>
          <li><strong>Correction:</strong> Request correction of inaccurate personal data</li>
          <li><strong>Deletion:</strong> Request deletion of your personal data and account</li>
          <li><strong>Export:</strong> Download your data in a machine-readable format (JSON/CSV)</li>
          <li><strong>Restriction:</strong> Request restriction of processing of your personal data</li>
          <li><strong>Objection:</strong> Object to processing of your personal data for specific purposes</li>
        </ul>
        <p>
          To exercise any of these rights, contact us at
          <a href="mailto:privacy@oracleflow.io" class="legal-link">privacy@oracleflow.io</a>.
          We will respond within 30 days.
        </p>
      </section>

      <section class="legal-section">
        <h2>8. Cookies</h2>
        <p>
          We use essential cookies for authentication and session management. We do not use third-party
          tracking cookies. LocalStorage is used to store user preferences and session tokens.
        </p>
      </section>

      <section class="legal-section">
        <h2>9. International Data Transfers</h2>
        <p>
          Your data may be transferred to and processed in countries other than your country of residence.
          We ensure appropriate safeguards are in place for such transfers, including standard contractual
          clauses where applicable.
        </p>
      </section>

      <section class="legal-section">
        <h2>10. Children's Privacy</h2>
        <p>
          The Service is not intended for individuals under the age of 18. We do not knowingly collect
          personal data from children. If you believe we have collected data from a child, please contact
          us immediately.
        </p>
      </section>

      <section class="legal-section">
        <h2>11. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of significant changes
          by email or through the Service. Continued use after changes constitutes acceptance of the
          revised policy.
        </p>
      </section>

      <section class="legal-section">
        <h2>12. Contact Us</h2>
        <p>
          For questions or concerns about this Privacy Policy, contact us at
          <a href="mailto:privacy@oracleflow.io" class="legal-link">privacy@oracleflow.io</a>.
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #d4d4d4;
  padding: 60px 24px;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.legal-container {
  max-width: 800px;
  margin: 0 auto;
}

.legal-title {
  font-size: 2.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
}

.legal-updated {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 48px;
}

.legal-section {
  margin-bottom: 36px;
}

.legal-section h2 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 12px;
}

.legal-section p {
  font-size: 0.95rem;
  line-height: 1.8;
  color: #a0a0a0;
}

.legal-section ul {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}

.legal-section ul li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 8px;
  font-size: 0.95rem;
  line-height: 1.7;
  color: #a0a0a0;
}

.legal-section ul li::before {
  content: '\2022';
  position: absolute;
  left: 0;
  color: #FF4500;
  font-weight: bold;
}

.legal-section strong {
  color: #d4d4d4;
}

.legal-link {
  color: #FF4500;
  text-decoration: none;
}

.legal-link:hover {
  text-decoration: underline;
}
</style>
