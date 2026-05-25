# ============================================
# FILE:
# app/api/routes/analytics.py
# ============================================

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.auth.admin_auth import verify_admin
from app.services.usage_service import UsageTracker

router = APIRouter()

# ============================================
# USAGE SUMMARY
# ============================================

@router.get("/summary")
async def usage_summary(
    days: int = Query(None, ge=1, le=365),
    admin=Depends(verify_admin),
):
    return UsageTracker.get_summary(days=days)

# ============================================
# RECENT LOGS
# ============================================

@router.get("/recent")
async def recent_usage(
    limit: int = Query(
        default=50, ge=1, le=200
    ),
    days: int = Query(None, ge=1, le=365),
    offset: int = Query(default=0, ge=0),
    admin=Depends(verify_admin),
):
    return UsageTracker.get_recent(limit=limit, days=days, offset=offset)

# ============================================
# DAILY STATS
# ============================================

@router.get("/daily")
async def daily_stats(
    days: int = Query(
        default=30, ge=1, le=365
    ),
    admin=Depends(verify_admin),
):
    return UsageTracker.get_daily_stats(days)

# ============================================
# DASHBOARD UI
# ============================================

@router.get("/dashboard", response_class=HTMLResponse)
async def analytics_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background-color: #f4f7f6; color: #333; }
            .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
            .container { max-width: 1000px; margin: 20px auto; padding: 0 20px; }
            .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .stat { font-size: 32px; font-weight: bold; color: #3498db; }
            .label { font-size: 14px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }
            th { background-color: #f8f9fa; font-weight: 600; color: #2c3e50; }
            .error { color: #e74c3c; font-weight: bold; }
            .success { color: #2ecc71; font-weight: bold; }
            .login-container { text-align: center; margin-top: 100px; }
            input[type="password"] { padding: 12px; width: 250px; border: 1px solid #bdc3c7; border-radius: 6px; font-size: 16px; outline: none; }
            input[type="password"]:focus { border-color: #3498db; }
            button { padding: 12px 24px; margin-left: 10px; background-color: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; transition: background 0.2s; }
            button:hover { background-color: #2980b9; }
        </style>
    </head>
    <body>
        <div id="auth-section" class="container login-container">
            <div class="card" style="display: inline-block; padding: 40px;">
                <h2 style="margin-top: 0; color: #2c3e50;">Admin Login</h2>
                <p style="color: #7f8c8d; margin-bottom: 20px;">Enter your Admin API Key to view analytics</p>
                <input type="password" id="admin-key" placeholder="Admin API Key">
                <button onclick="loadDashboard()">Login</button>
                <p id="auth-error" class="error" style="margin-top: 15px; min-height: 20px;"></p>
            </div>
        </div>

        <div id="dashboard-section" style="display: none;">
            <div class="header">
                <h1 style="margin: 0;">Chatbot Analytics Dashboard</h1>
            </div>
            
            <div class="container">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-bottom: 20px;">
                        <h3 style="margin: 0; color: #2c3e50;">Overview</h3>
                        <select id="date-filter" onchange="loadDashboard(this.value)" style="padding: 8px; border-radius: 6px; border: 1px solid #bdc3c7; outline: none; font-size: 14px; background: #fff;">
                            <option value="">All Time</option>
                            <option value="1">Last 24 Hours</option>
                            <option value="7">Last 7 Days</option>
                            <option value="30">Last 30 Days</option>
                        </select>
                    </div>
                    <div class="grid" id="summary-grid">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <div class="card">
                    <h3 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px;">Recent Interactions</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Date & Time</th>
                                <th>Session ID</th>
                                <th>User Message</th>
                                <th>Latency</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="recent-tbody">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                    
                    <!-- Pagination Controls -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #ecf0f1;">
                        <button id="prev-page" onclick="changePage(-1)" style="padding: 8px 16px; background-color: #ecf0f1; color: #2c3e50; font-size: 14px;" disabled>Previous</button>
                        <span id="page-info" style="color: #7f8c8d; font-size: 14px;">Page 1</span>
                        <button id="next-page" onclick="changePage(1)" style="padding: 8px 16px; background-color: #ecf0f1; color: #2c3e50; font-size: 14px;" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentDays = "";
            let currentPage = 1;
            const itemsPerPage = 15;
            let totalMessages = 0;
            
            async function fetchAPI(endpoint) {
                const key = document.getElementById('admin-key').value;
                const response = await fetch(endpoint, {
                    headers: { 'x-admin-key': key }
                });
                if (!response.ok) throw new Error('Unauthorized');
                return await response.json();
            }
            
            function changePage(direction) {
                currentPage += direction;
                loadDashboard(null, true);
            }

            async function loadDashboard(days = null, isPagination = false) {
                if (days !== null) {
                    currentDays = days;
                    currentPage = 1; // Reset to page 1 on filter change
                }
                
                const errorEl = document.getElementById('auth-error');
                const key = document.getElementById('admin-key').value;
                if (!key) {
                    errorEl.textContent = 'Please enter an API key.';
                    return;
                }
                
                if (!isPagination) {
                    errorEl.textContent = 'Loading...';
                    errorEl.style.color = '#7f8c8d';
                }
                
                try {
                    let summaryUrl = '/analytics/summary';
                    let offset = (currentPage - 1) * itemsPerPage;
                    let recentUrl = `/analytics/recent?limit=${itemsPerPage}&offset=${offset}`;
                    
                    if (currentDays) {
                        summaryUrl += `?days=${currentDays}`;
                        recentUrl += `&days=${currentDays}`;
                    }
                    
                    const summary = await fetchAPI(summaryUrl);
                    totalMessages = summary.total_messages;
                    const recent = await fetchAPI(recentUrl);
                    
                    document.getElementById('auth-section').style.display = 'none';
                    document.getElementById('dashboard-section').style.display = 'block';
                    
                    // Render Summary
                    document.getElementById('summary-grid').innerHTML = `
                        <div><div class="stat">${summary.total_messages}</div><div class="label">Total Messages</div></div>
                        <div><div class="stat">${summary.unique_sessions}</div><div class="label">Unique Sessions</div></div>
                        <div><div class="stat">${summary.avg_response_time_ms} ms</div><div class="label">Avg Latency</div></div>
                        <div><div class="stat">${summary.success_rate}%</div><div class="label">Success Rate</div></div>
                        <div><div class="stat">${summary.total_input_tokens || 0}</div><div class="label">Input Tokens</div></div>
                        <div><div class="stat">${summary.total_output_tokens || 0}</div><div class="label">Output Tokens</div></div>
                    `;
                    
                    // Render Recent
                    const tbody = document.getElementById('recent-tbody');
                    tbody.innerHTML = '';
                    recent.forEach(log => {
                        const date = new Date(log.created_at).toLocaleString();
                        const statusClass = log.status === 'success' ? 'success' : 'error';
                        const session = log.session_id ? log.session_id.substring(0, 8) + '...' : 'N/A';
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="color: #7f8c8d; font-size: 14px;">${date}</td>
                            <td><code style="background: #f4f7f6; padding: 2px 6px; border-radius: 4px;">${session}</code></td>
                            <td>${log.user_message}</td>
                            <td>${log.response_time_ms} ms</td>
                            <td class="${statusClass}">${log.status.toUpperCase()}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                    
                    // Update Pagination Controls
                    document.getElementById('page-info').textContent = `Page ${currentPage} of ${Math.ceil(totalMessages / itemsPerPage) || 1}`;
                    
                    const prevBtn = document.getElementById('prev-page');
                    const nextBtn = document.getElementById('next-page');
                    
                    prevBtn.disabled = currentPage === 1;
                    prevBtn.style.opacity = prevBtn.disabled ? '0.5' : '1';
                    prevBtn.style.cursor = prevBtn.disabled ? 'not-allowed' : 'pointer';
                    
                    nextBtn.disabled = (currentPage * itemsPerPage) >= totalMessages;
                    nextBtn.style.opacity = nextBtn.disabled ? '0.5' : '1';
                    nextBtn.style.cursor = nextBtn.disabled ? 'not-allowed' : 'pointer';
                    
                } catch (err) {
                    errorEl.style.color = '#e74c3c';
                    errorEl.textContent = 'Invalid Admin Key or Error Loading Data';
                }
            }
            
            // Allow pressing Enter to login
            document.getElementById('admin-key').addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    loadDashboard();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
