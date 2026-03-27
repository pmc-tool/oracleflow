<template>
  <div class="legal-page">
    <div class="legal-container">
      <h1 class="legal-title">Terms of Service</h1>
      <p class="legal-updated">Last updated: March 26, 2026</p>

      <section class="legal-section">
        <h2>1. Acceptance of Terms</h2>
        <p>
          By accessing or using OracleFlow ("the Service"), you agree to be bound by these Terms of Service.
          If you do not agree to these terms, do not use the Service. We reserve the right to update these
          terms at any time, and continued use constitutes acceptance of the revised terms.
        </p>
      </section>

      <section class="legal-section">
        <h2>2. Description of Service</h2>
        <p>
          OracleFlow is a geopolitical intelligence and web monitoring platform that provides automated
          site monitoring, signal detection, entity tracking, and simulation capabilities. The Service
          is provided on a software-as-a-service (SaaS) basis.
        </p>
      </section>

      <section class="legal-section">
        <h2>3. Account Responsibilities</h2>
        <p>
          You are responsible for maintaining the confidentiality of your account credentials and for all
          activities that occur under your account. You must provide accurate and complete information when
          creating your account. You agree to notify us immediately of any unauthorized use of your account.
        </p>
      </section>

      <section class="legal-section">
        <h2>4. Use of Service</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use the Service for any unlawful purpose or in violation of any applicable laws</li>
          <li>Attempt to reverse-engineer, decompile, or disassemble any part of the Service</li>
          <li>Use the Service to scrape, monitor, or collect data from websites you do not own or have permission to access</li>
          <li>Interfere with or disrupt the integrity or performance of the Service</li>
          <li>Share your account credentials with third parties</li>
          <li>Resell or redistribute the Service without prior written consent</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>5. Payment Terms</h2>
        <p>
          Paid plans are billed on a monthly or annual basis. All fees are non-refundable except as required
          by law or as explicitly stated in our refund policy. You authorize us to charge your payment method
          on a recurring basis. We may change pricing with 30 days' notice.
        </p>
      </section>

      <section class="legal-section">
        <h2>6. Refund Policy</h2>
        <p>
          You may request a refund within 14 days of your initial subscription purchase if you are not
          satisfied with the Service. Refunds are not available for renewal periods. To request a refund,
          contact our support team at support@oracleflow.io.
        </p>
      </section>

      <section class="legal-section">
        <h2>7. Intellectual Property</h2>
        <p>
          The Service, including its original content, features, and functionality, is owned by OracleFlow
          and is protected by international copyright, trademark, patent, trade secret, and other intellectual
          property laws. Your data remains yours; you grant us a limited license to process it solely to
          provide the Service.
        </p>
      </section>

      <section class="legal-section">
        <h2>8. Limitation of Liability</h2>
        <p>
          To the maximum extent permitted by law, OracleFlow shall not be liable for any indirect, incidental,
          special, consequential, or punitive damages, including loss of profits, data, or goodwill, arising
          from your use of the Service. Our total liability shall not exceed the amount paid by you in the
          twelve (12) months preceding the claim.
        </p>
      </section>

      <section class="legal-section">
        <h2>9. Disclaimer of Warranties</h2>
        <p>
          The Service is provided "as is" and "as available" without warranties of any kind, either express
          or implied, including but not limited to implied warranties of merchantability, fitness for a
          particular purpose, and non-infringement. We do not guarantee the accuracy, completeness, or
          reliability of intelligence data or simulation results.
        </p>
      </section>

      <section class="legal-section">
        <h2>10. Termination</h2>
        <p>
          We may terminate or suspend your account at any time, with or without cause, with or without notice.
          Upon termination, your right to use the Service ceases immediately. You may terminate your account
          at any time by contacting support. Data will be retained for 30 days after termination, after which
          it will be permanently deleted.
        </p>
      </section>

      <section class="legal-section">
        <h2>11. Governing Law</h2>
        <p>
          These Terms shall be governed by and construed in accordance with the laws of the State of Delaware,
          United States, without regard to its conflict of law provisions.
        </p>
      </section>

      <section class="legal-section">
        <h2>12. Contact</h2>
        <p>
          For questions about these Terms, contact us at
          <a href="mailto:legal@oracleflow.io" class="legal-link">legal@oracleflow.io</a>.
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

.legal-link {
  color: #FF4500;
  text-decoration: none;
}

.legal-link:hover {
  text-decoration: underline;
}
</style>
