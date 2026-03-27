<template>
  <div class="not-found-page">
    <div class="not-found-card">
      <div class="error-code">404</div>
      <div class="error-divider"></div>
      <h1 class="error-title">Page Not Found</h1>
      <p class="error-desc">The route you requested does not exist.</p>
      <div class="error-actions">
        <router-link to="/intel" class="error-link">Go to Intel</router-link>
        <router-link to="/" class="error-link secondary">Home</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  min-height: 100vh;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace;
  padding: 20px;
}

.not-found-card {
  text-align: center;
  max-width: 440px;
}

.error-code {
  font-size: 6rem;
  font-weight: 800;
  color: #FF4500;
  letter-spacing: 4px;
  line-height: 1;
  margin-bottom: 16px;
}

.error-divider {
  width: 60px;
  height: 2px;
  background: #333;
  margin: 0 auto 20px;
}

.error-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #e8e8e8;
  margin: 0 0 10px;
  letter-spacing: 1px;
}

.error-desc {
  font-size: 0.85rem;
  color: #666;
  margin: 0 0 32px;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.error-link {
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  color: #fff;
  background: #FF4500;
  text-decoration: none;
  padding: 10px 24px;
  border-radius: 3px;
  transition: background 0.2s;
  letter-spacing: 0.5px;
}

.error-link:hover {
  background: #e03e00;
}

.error-link.secondary {
  background: transparent;
  border: 1px solid #333;
  color: #999;
}

.error-link.secondary:hover {
  border-color: #666;
  color: #e8e8e8;
}
</style>
