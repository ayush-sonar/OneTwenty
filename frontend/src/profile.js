import api from './api.js';

export function renderProfilePage() {
  const app = document.querySelector('#app');

  app.innerHTML = `
    <div class="dashboard">
      <header class="dashboard-header">
        <h1 id="logo" style="cursor: pointer;">🩸 Nightscout</h1>
        <div class="header-actions">
          <button id="back-to-dashboard" class="btn-secondary">← Dashboard</button>
          <button id="logout-btn" class="btn-secondary">Logout</button>
        </div>
      </header>
      
      <main class="dashboard-main">
        <div class="profile-container">
          <h2>My Profile</h2>
          
          <div class="profile-section">
            <h3>API Secret</h3>
            <p class="section-description">
              Use this API secret to upload CGM data from your devices (xDrip, Nightscout uploader, etc.)
            </p>
            
            <div id="api-secret-container">
              <button id="get-api-secret-btn" class="btn-primary">Show API Secret</button>
            </div>
            
            <div id="api-secret-display" class="hidden">
              <div class="secret-box">
                <label>Your API Secret:</label>
                <div class="secret-value">
                  <code id="api-secret-value">Loading...</code>
                  <button id="copy-secret-btn" class="btn-icon" title="Copy to clipboard">
                    📋
                  </button>
                </div>
              </div>
              
              <div class="secret-actions">
                <button id="reset-api-secret-btn" class="btn-danger">
                  🔄 Reset API Secret
                </button>
                <p class="warning-text">⚠️ Resetting will invalidate your current secret and break existing integrations!</p>
              </div>
            </div>
          </div>
          
          <div class="profile-section">
            <h3>Your Nightscout URL</h3>
            <p class="section-description">
              Share this URL with your devices and apps to access your CGM data
            </p>
            <div class="secret-box">
              <label>Subdomain URL:</label>
              <div class="secret-value">
                <code id="subdomain-url">Loading...</code>
                <button id="copy-url-btn" class="btn-icon" title="Copy to clipboard">
                  📋
                </button>
              </div>
            </div>
          </div>
          
          <div class="profile-section">
            <h3>Account Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>Email:</label>
                <span id="user-email">Loading...</span>
              </div>
              <div class="info-item">
                <label>Role:</label>
                <span id="user-role">user</span>
              </div>
              <div class="info-item">
                <label>Tier:</label>
                <span id="user-tier">free</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  `;

  // Event listeners
  document.getElementById('logo').addEventListener('click', () => {
    window.location.reload(); // Go back to dashboard
  });

  document.getElementById('back-to-dashboard').addEventListener('click', () => {
    window.location.reload(); // Reload to go back to dashboard
  });

  document.getElementById('logout-btn').addEventListener('click', () => {
    api.logout();
    window.location.reload();
  });

  document.getElementById('get-api-secret-btn').addEventListener('click', async () => {
    await showApiSecret();
  });

  document.getElementById('reset-api-secret-btn')?.addEventListener('click', async () => {
    if (confirm('Are you sure you want to reset your API secret? This will break existing integrations!')) {
      await resetApiSecret();
    }
  });

  document.getElementById('copy-secret-btn')?.addEventListener('click', () => {
    const secret = document.getElementById('api-secret-value').textContent;
    const btn = document.getElementById('copy-secret-btn');

    navigator.clipboard.writeText(secret).then(() => {
      // Visual feedback
      const originalText = btn.textContent;
      btn.textContent = '✓';
      btn.style.background = 'var(--success-color)';

      setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = '';
      }, 2000);
    });
  });

  // Load user info
  loadUserInfo();
}

async function showApiSecret() {
  try {
    const response = await api.getApiSecret();
    const secretValue = response.api_secret;

    document.getElementById('api-secret-value').textContent = secretValue;
    document.getElementById('api-secret-container').classList.add('hidden');
    document.getElementById('api-secret-display').classList.remove('hidden');
  } catch (error) {
    alert('Failed to load API secret: ' + error.message);
  }
}

async function resetApiSecret() {
  try {
    const response = await api.resetApiSecret();
    const newSecret = response.api_secret;

    document.getElementById('api-secret-value').textContent = newSecret;
    alert('API Secret has been reset successfully!');
  } catch (error) {
    alert('Failed to reset API secret: ' + error.message);
  }
}

async function loadUserInfo() {
  try {
    // Load profile data including subdomain URL
    const profile = await api.getProfile();

    // Update subdomain URL
    if (profile.subdomain_url) {
      document.getElementById('subdomain-url').textContent = profile.subdomain_url;

      // Add copy URL button listener
      document.getElementById('copy-url-btn').addEventListener('click', () => {
        const url = profile.subdomain_url;
        const btn = document.getElementById('copy-url-btn');

        navigator.clipboard.writeText(url).then(() => {
          // Visual feedback
          const originalText = btn.textContent;
          btn.textContent = '✓';
          btn.style.background = 'var(--success-color)';

          setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
          }, 2000);
        });
      });
    }

    // Load status for user email
    const status = await api.getStatus();
    document.getElementById('user-email').textContent = status.name || 'User';
  } catch (error) {
    console.error('Failed to load user info:', error);
    document.getElementById('subdomain-url').textContent = 'Error loading URL';
    document.getElementById('user-email').textContent = 'Error loading email';
  }
}
