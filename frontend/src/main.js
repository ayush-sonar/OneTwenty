import './style.css'
import './responsive.css'
import api from './api.js'
import { SimpleGlucoseChart } from './simple-chart.js'

const app = document.querySelector('#app');

// Check if user is logged in
if (api.isAuthenticated()) {
  loadDashboard();
} else {
  showLoginPage();
}

function showLoginPage() {
  app.innerHTML = `
    <div class="login-container">
      <div class="login-card">
        <h1>🩸 Nightscout SaaS</h1>
        <p class="subtitle">Continuous Glucose Monitoring</p>
        
        <div id="error-message" class="error hidden"></div>
        
        <form id="login-form">
          <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" required placeholder="you@example.com" />
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" required placeholder="••••••••" />
          </div>
          
          <button type="submit" class="btn-primary">Login</button>
        </form>
        
        <p class="signup-link">
          Don't have an account? <a href="#" id="show-signup">Sign up</a>
        </p>
      </div>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('show-signup').addEventListener('click', (e) => {
    e.preventDefault();
    showSignupPage();
  });
}

function showSignupPage() {
  app.innerHTML = `
    <div class="login-container">
      <div class="login-card">
        <h1>🩸 Create Account</h1>
        <p class="subtitle">Start monitoring your glucose</p>
        
        <div id="error-message" class="error hidden"></div>
        <div id="success-message" class="success hidden"></div>
        
        <form id="signup-form">
          <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" required placeholder="you@example.com" />
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" required placeholder="••••••••" minlength="8" />
          </div>
          
          <button type="submit" class="btn-primary">Sign Up</button>
        </form>
        
        <p class="signup-link">
          Already have an account? <a href="#" id="show-login">Login</a>
        </p>
      </div>
    </div>
  `;

  document.getElementById('signup-form').addEventListener('submit', handleSignup);
  document.getElementById('show-login').addEventListener('click', (e) => {
    e.preventDefault();
    showLoginPage();
  });
}

async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const errorDiv = document.getElementById('error-message');

  try {
    await api.login(email, password);
    loadDashboard();
  } catch (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
  }
}

async function handleSignup(e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const errorDiv = document.getElementById('error-message');
  const successDiv = document.getElementById('success-message');

  try {
    await api.signup(email, password);
    successDiv.textContent = 'Account created! Please login.';
    successDiv.classList.remove('hidden');

    setTimeout(() => showLoginPage(), 2000);
  } catch (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
  }
}

async function loadDashboard() {
  const app = document.querySelector('#app');

  app.innerHTML = `
    <div class="dashboard">
      <div class="menu-overlay" id="menu-overlay"></div>
      <header class="dashboard-header">
        <h1 id="logo" style="cursor: pointer;">🩸 Nightscout</h1>
        <div class="header-actions mobile-menu" id="header-actions">
          <button id="profile-btn" class="btn-secondary">Profile</button>
          <button id="logout-btn" class="btn-secondary">Logout</button>
        </div>
        <button id="menu-btn" class="btn-icon hamburger">☰</button>
      </header>
      
      <main class="dashboard-main">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value" id="last-reading">--</div>
          </div>
          <div class="stat-card">
            <div class="stat-value trend-arrow" id="trend">--</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="current-bg">--</div>
          </div>
        </div>

        <div class="date-picker-container">
          <div class="date-picker">
            <button class="date-nav-btn" id="prev-date">←</button>
            <div class="date-display" id="date-display">Today</div>
            <button class="date-nav-btn" id="next-date">→</button>
          </div>
        </div>

        <div class="time-range-container">
          <div class="time-range-selector">
            <button class="time-btn active" data-hours="2">2hr</button>
            <button class="time-btn" data-hours="4">4hr</button>
            <button class="time-btn" data-hours="6">6hr</button>
            <button class="time-btn" data-hours="8">8hr</button>
            <button class="time-btn" data-hours="12">12hr</button>
            <button class="time-btn" data-hours="24">24hr</button>
          </div>
        </div>

        <div class="chart-container">
          <div id="glucose-chart"></div>
        </div>
      </main>
    </div>
  `;

  // Hamburger menu toggle with slide-in behavior
  const menuBtn = document.getElementById('menu-btn');
  const menuActions = document.getElementById('header-actions');
  const menuOverlay = document.getElementById('menu-overlay');

  menuBtn.addEventListener('click', () => {
    menuActions.classList.toggle('show');
    menuOverlay.classList.toggle('show');
  });

  menuOverlay.addEventListener('click', () => {
    menuActions.classList.remove('show');
    menuOverlay.classList.remove('show');
  });

  document.getElementById('logo').addEventListener('click', () => {
    window.location.reload();
  });

  document.getElementById('profile-btn').addEventListener('click', () => {
    menuActions.classList.remove('show');
    menuOverlay.classList.remove('show');
    import('./profile.js').then(module => {
      module.renderProfilePage();
    });
  });

  document.getElementById('logout-btn').addEventListener('click', () => {
    menuActions.classList.remove('show');
    menuOverlay.classList.remove('show');
    // Disconnect WebSocket before logout
    import('./websocket.js').then(module => {
      module.default.disconnect();
    });
    api.logout();
    showLoginPage();
  });

  // Show loading state
  const statsGrid = document.querySelector('.stats-grid');
  const chartContainer = document.querySelector('.chart-container');

  statsGrid.innerHTML = '<div class="loading-message">⏳ Connecting to server...</div>';
  chartContainer.innerHTML = '<div class="loading-message">⏳ Loading glucose data...</div>';

  // Load data
  try {
    const status = await api.getStatus();

    // Restore stats grid
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div class="stat-value" id="last-reading">--</div>
      </div>
      <div class="stat-card">
        <div class="stat-value trend-arrow" id="trend">--</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="current-bg">--</div>
      </div>
    `;

    // Restore chart container
    chartContainer.innerHTML = `
      <div id="glucose-chart"></div>
    `;

    // Initialize chart with simple implementation
    const chart = new SimpleGlucoseChart('glucose-chart');
    chart.init();

    const entries = await api.getEntries({ hours: 2 }); // Default 2 hours

    // Update chart
    chart.updateData(entries);

    // Set up WebSocket for real-time updates
    import('./websocket.js').then(module => {
      const ws = module.default;

      // Connect WebSocket with JWT token
      ws.connect(api.token);

      // Listen for new entries
      ws.on('new_entry', (entry) => {
        console.log('[Dashboard] New entry received:', entry);

        // Add new entry to chart
        chart.addEntry(entry);

        // Update stat cards with latest reading
        updateStatCards(entry);
      });

      // Connection status
      ws.on('connected', () => {
        console.log('[Dashboard] WebSocket connected');
        // Could show a "Live" indicator here
      });

      ws.on('disconnected', () => {
        console.log('[Dashboard] WebSocket disconnected');
        // Could show a "Reconnecting..." indicator here
      });
    });

    // Set up drag callback to update stat cards
    chart.onNowLineDrag = (reading) => {
      if (reading) {
        updateStatCards(reading);
      }
    };

    // Display table
    displayEntries(entries);

    // Set up time range buttons
    let currentHours = 2; // Default 2 hours
    let selectedDate = null; // Track selected date

    // Date picker functionality
    const dateDisplay = document.getElementById('date-display');
    const prevDateBtn = document.getElementById('prev-date');
    const nextDateBtn = document.getElementById('next-date');

    function formatDateDisplay(date) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const compareDate = new Date(date);
      compareDate.setHours(0, 0, 0, 0);

      if (compareDate.getTime() === today.getTime()) {
        return 'Today';
      }

      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      if (compareDate.getTime() === yesterday.getTime()) {
        return 'Yesterday';
      }

      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      if (compareDate.getTime() === tomorrow.getTime()) {
        return 'Tomorrow';
      }

      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    async function loadDateData(date) {
      selectedDate = date;
      dateDisplay.textContent = formatDateDisplay(date);

      // Auto-switch to 24hr view
      document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
      const btn24hr = document.querySelector('.time-btn[data-hours="24"]');
      btn24hr.classList.add('active');
      currentHours = 24;

      // Fetch data for the specific date (00:00 to 23:59) using Unix timestamps
      const startOfDay = new Date(date);
      startOfDay.setHours(0, 0, 0, 0);
      const endOfDay = new Date(date);
      endOfDay.setHours(23, 59, 59, 999);

      // Convert to Unix timestamps in milliseconds
      const startMs = startOfDay.getTime();
      const endMs = endOfDay.getTime();

      const dateEntries = await api.getEntries({
        start: startMs.toString(),
        end: endMs.toString()
      });

      chart.updateData(dateEntries);
      displayEntries(dateEntries);
    }

    prevDateBtn.addEventListener('click', () => {
      const currentDate = selectedDate || new Date();
      const prevDate = new Date(currentDate);
      prevDate.setDate(prevDate.getDate() - 1);
      loadDateData(prevDate);
    });

    nextDateBtn.addEventListener('click', () => {
      const currentDate = selectedDate || new Date();
      const nextDate = new Date(currentDate);
      nextDate.setDate(nextDate.getDate() + 1);
      loadDateData(nextDate);
    });

    dateDisplay.addEventListener('click', () => {
      // Reset to "Today" and current time range
      selectedDate = null;
      dateDisplay.textContent = 'Today';

      // Reload with current hours setting
      api.getEntries({ hours: currentHours }).then(newEntries => {
        chart.updateData(newEntries);
        displayEntries(newEntries);
      });
    });

    document.querySelectorAll('.time-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        // Only allow time range selection if no specific date is selected
        if (selectedDate) {
          // If a date is selected, clicking time range resets to today
          selectedDate = null;
          dateDisplay.textContent = 'Today';
        }

        // Update active state
        document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Get selected hours
        currentHours = parseInt(btn.dataset.hours);

        // Fetch data for the selected time range using hours parameter
        const newEntries = await api.getEntries({ hours: currentHours });

        // Update chart
        chart.updateData(newEntries);
        displayEntries(newEntries);
      });
    });

    // Handle window resize
    window.addEventListener('resize', () => chart.resize());
  } catch (error) {
    console.error('Failed to load dashboard:', error);

    // Show error in UI
    statsGrid.innerHTML = '<div class="error-message">❌ Failed to connect to server</div>';
    chartContainer.innerHTML = '<div class="error-message">❌ Failed to load data</div>';

    // Check if it's an auth error (401/403)
    if (error.message.includes('401') || error.message.includes('403') || error.message.includes('Unauthorized')) {
      api.logout();
      showLoginPage();
    } else {
      // Show error but don't log out
      console.error('Dashboard error details:', error);
    }
  }
}

function updateStatCards(reading) {
  const now = Date.now();
  const ageMinutes = (now - new Date(reading.date)) / (1000 * 60);
  const isCurrent = ageMinutes < 15;

  // Update time (without seconds)
  const timeElement = document.getElementById('last-reading');
  const readingDate = new Date(reading.date);
  const timeString = readingDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  timeElement.textContent = timeString;
  timeElement.style.color = isCurrent ? '#ffffff' : '#808080';

  // Update trend
  const trendArrows = {
    'DoubleUp': '⇈',
    'SingleUp': '↑',
    'FortyFiveUp': '↗',
    'Flat': '→',
    'FortyFiveDown': '↘',
    'SingleDown': '↓',
    'DoubleDown': '⇊'
  };
  document.getElementById('trend').textContent = trendArrows[reading.direction] || '→';

  // Color-code BG: green (in range), yellow (warning), red (urgent)
  const bgElement = document.getElementById('current-bg');
  const bgCard = bgElement.closest('.stat-card');
  bgElement.textContent = `${reading.sgv} mg/dL`;

  // Determine BG color based on ranges (typical Nightscout ranges)
  let bgColor, bgBackground;
  if (reading.sgv < 55) {
    // Urgent low
    bgColor = '#ffffff';
    bgBackground = '#d9534f'; // Red
  } else if (reading.sgv < 80) {
    // Low warning
    bgColor = '#ffffff';
    bgBackground = '#f0ad4e'; // Yellow/Orange
  } else if (reading.sgv <= 180) {
    // In range
    bgColor = isCurrent ? '#ffffff' : '#808080';
    bgBackground = '#5cb85c'; // Green
  } else if (reading.sgv <= 260) {
    // High warning
    bgColor = '#ffffff';
    bgBackground = '#f0ad4e'; // Yellow/Orange
  } else {
    // Urgent high
    bgColor = '#ffffff';
    bgBackground = '#d9534f'; // Red
  }

  bgElement.style.color = bgColor;
  bgCard.style.backgroundColor = bgBackground;
  bgCard.style.border = `2px solid ${bgBackground}`;
}

function displayEntries(entries) {
  if (!entries || entries.length === 0) return;

  // Display current BG - use LAST entry (newest)
  const latest = entries[entries.length - 1];
  updateStatCards(latest);
}
