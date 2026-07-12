window.onerror = function(msg, url, line, col, error) {
    if(!msg.includes('ResizeObserver')) {
        alert("CRITICAL JS ERROR: " + msg + "\nLine: " + line);
    }
    return false;
};

// Execute theme check immediately on load to prevent FOUC
(function initTheme() {
    const savedTheme = localStorage.getItem('jhire_theme') || 'auto';
    applyTheme(savedTheme);
})();

function applyTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else if (theme === 'light') {
        document.documentElement.classList.remove('dark');
    } else { // auto
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }
}

window.changeTheme = function(theme) {
    localStorage.setItem('jhire_theme', theme);
    applyTheme(theme);
    if(window.updateThemeUI) window.updateThemeUI(theme); // Optional update for buttons
};

window.updateThemeUI = function(theme) {
    const btns = {
        'light': document.getElementById('themeBtn-light'),
        'dark': document.getElementById('themeBtn-dark'),
        'auto': document.getElementById('themeBtn-auto')
    };
    for (const key in btns) {
        if (btns[key]) {
            if (key === theme) {
                // Change border styling to indicate selection. Using generic solid tailwind colors to avoid hex opacity parse errors
                btns[key].style.border = '2px solid #003461'; // primary color
                btns[key].style.backgroundColor = 'rgba(0, 52, 97, 0.1)';
            } else {
                btns[key].style.border = '';
                btns[key].style.backgroundColor = '';
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Initial call to set active button state
    const savedTheme = localStorage.getItem('jhire_theme') || 'auto';
    if(window.updateThemeUI) window.updateThemeUI(savedTheme);

    // --- Sidebar Active State ---
    (function highlightActiveSidebarLink() {
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        const sidebarLinks = document.querySelectorAll('aside nav a, aside .p-4 a, aside div.p-4 a');
        const ACTIVE_CLASSES = ['bg-primary/10', 'text-primary', 'shadow-sm'];
        const INACTIVE_CLASSES = ['text-on-surface-variant', 'hover:bg-surface-container', 'hover:text-on-surface'];

        sidebarLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (!href) return;
            const linkPage = href.split('/').pop();

            // Remove any existing active state
            ACTIVE_CLASSES.forEach(cls => link.classList.remove(cls));

            if (linkPage === currentPage) {
                // Apply active state
                INACTIVE_CLASSES.forEach(cls => link.classList.remove(cls));
                ACTIVE_CLASSES.forEach(cls => link.classList.add(cls));
            } else {
                // Ensure inactive state
                INACTIVE_CLASSES.forEach(cls => {
                    if (!link.classList.contains(cls)) link.classList.add(cls);
                });
            }
        });
    })();

    // --- Mobile Menu Logic ---
    const openMobileMenuBtn = document.getElementById('openMobileMenuBtn');
    const closeMobileMenuBtn = document.getElementById('closeMobileMenuBtn');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobileMenuSidebar = document.getElementById('mobileMenuSidebar');

    const toggleMobileMenu = () => {
        const isHidden = mobileMenuOverlay.classList.contains('hidden');
        if (isHidden) {
            mobileMenuOverlay.classList.remove('hidden');
            // Allow paint then transition opacity
            requestAnimationFrame(() => {
                mobileMenuOverlay.classList.remove('opacity-0');
                mobileMenuSidebar.classList.remove('translate-x-full');
            });
            document.body.style.overflow = 'hidden'; // Stop scrolling
        } else {
            mobileMenuOverlay.classList.add('opacity-0');
            mobileMenuSidebar.classList.add('translate-x-full');
            setTimeout(() => {
                mobileMenuOverlay.classList.add('hidden');
                document.body.style.overflow = '';
            }, 300);
        }
    };

    if (openMobileMenuBtn && mobileMenuSidebar) {
        openMobileMenuBtn.addEventListener('click', toggleMobileMenu);
        closeMobileMenuBtn.addEventListener('click', toggleMobileMenu);
        mobileMenuOverlay.addEventListener('click', toggleMobileMenu);
    }


    const token = localStorage.getItem('jhire_jwt_token');
    let currentUser = null;

    if (token) {
        try {
            currentUser = JSON.parse(atob(token.split('.')[1]));
            
            // Auto redirect from login page if already logged in
            if (window.location.pathname.includes('login.html')) {
                if (currentUser.role === 'admin') {
                    window.location.href = 'dashboard.html';
                } else {
                    window.location.href = 'inicio.html';
                }
                return; // Stop execution on this page
            }
            
            // ADMIN ROUTE GUARD: Block non-admin users from admin pages
            const adminPages = ['dashboard.html', 'crm.html', 'facturacion.html', 'inventario.html', 'ventas.html', 'admin_catalogo.html', 'admin_usuarios.html', 'admin_perfil.html'];
            const currentPage = window.location.pathname.split('/').pop();
            
            if (adminPages.includes(currentPage) && currentUser.role !== 'admin') {
                window.location.href = 'inicio.html';
                return; // Stop all execution
            }
            
            // Update Profile UI anywhere
            const userFullName = currentUser.first_name ? `${currentUser.first_name} ${currentUser.last_name || ''}`.trim() : currentUser.sub;
            
            const headerUserName = document.getElementById('headerUserName');
            if (headerUserName) headerUserName.innerText = userFullName;

            const headerUserRole = document.getElementById('headerUserRole');
            if (headerUserRole) headerUserRole.innerText = currentUser.role === 'admin' ? 'Administrador' : 'Customer';

            const userAvatarImg = document.getElementById('userAvatar');
            if (userAvatarImg) {
                userAvatarImg.src = currentUser.profile_picture_url || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(userFullName) + '&background=003461&color=fff';
            }

            const avatarContainer = document.getElementById('avatarContainer');
            const logoutDropdown = document.getElementById('logoutDropdown');
            const logoutBtn = document.getElementById('logoutBtn');

            if (avatarContainer && logoutDropdown) {
                avatarContainer.addEventListener('click', () => {
                    logoutDropdown.classList.toggle('hidden');
                });
                
                // Close dropdown if clicking outside
                document.addEventListener('click', (e) => {
                    if (!avatarContainer.contains(e.target) && !logoutDropdown.contains(e.target)) {
                        logoutDropdown.classList.add('hidden');
                    }
                });
            }

            if (logoutBtn) {
                logoutBtn.addEventListener('click', () => {
                    localStorage.removeItem('jhire_jwt_token');
                    window.location.href = 'inicio.html';
                });
            }

        } catch (e) {
            console.error("Invalid token", e);
            localStorage.removeItem('jhire_jwt_token');
        }
    } else {
        // Unauthenticated visitor
        // 1. Redirect if trying to access protected pages
        const path = window.location.pathname;
        if (path.includes('dashboard.html') || path.includes('mis_pedidos.html')) {
            window.location.href = 'login.html';
            return;
        }

        // 2. Hide User Avatar & Show Login Button instead
        const avatarContainer = document.getElementById('avatarContainer');
        if (avatarContainer) avatarContainer.style.display = 'none';
        
        const headerUserName = document.getElementById('headerUserName');
        if (headerUserName) headerUserName.style.display = 'none';

        const navActions = document.querySelector('nav .flex.items-center.gap-6 > .flex.items-center.gap-4.relative') || document.querySelector('nav .flex.items-center.gap-8')?.nextElementSibling?.firstElementChild;
        if (navActions && !document.getElementById('navLoginBtn')) {
            navActions.insertAdjacentHTML('beforeend', '<a id="navLoginBtn" href="login.html" class="px-5 py-2 bg-primary text-white text-xs font-bold rounded-full hover:shadow-md hover:-translate-y-0.5 transition-all">Iniciar Sesión</a>');
        }
    }

    // Login Form Logic
    const loginForm = document.getElementById('loginForm');
    const submitBtn = document.getElementById('submitBtn');
    const errorBox = document.getElementById('errorBox');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-sm">refresh</span> PROCESANDO...`;
            submitBtn.disabled = true;
            errorBox.classList.add('hidden');
            
            try {
                // Login Request 
                const formData = new URLSearchParams();
                formData.append('username', email); // FastAPI OAuth2 uses 'username' mapped to our email (giampier)
                formData.append('password', password);
                
                const loginRes = await fetch('/api/auth/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });
                
                const loginData = await loginRes.json();
                if (!loginRes.ok) throw new Error(loginData.detail || 'Credenciales incorrectas');
                
                // Securely store the JWT Access Token
                localStorage.setItem('jhire_jwt_token', loginData.access_token);
                
                // Role-based redirection
                if (loginData.role === 'admin') {
                    window.location.href = 'dashboard.html';
                } else {
                    window.location.href = 'inicio.html';
                }
                
            } catch (err) {
                errorBox.innerText = err.message;
                errorBox.classList.remove('hidden');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Register Logic inside Login Page
    const btnOpenRegister = document.getElementById('btnOpenRegister');
    const registerModal = document.getElementById('registerModal');
    const closeRegisterModal = document.getElementById('closeRegisterModal');
    const registerForm = document.getElementById('registerForm');

    if (btnOpenRegister && registerModal) {
        btnOpenRegister.addEventListener('click', () => registerModal.classList.remove('hidden'));
        closeRegisterModal.addEventListener('click', () => registerModal.classList.add('hidden'));

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = registerForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = 'Registrando...';
            btn.disabled = true;

            const errBox = document.getElementById('registerErrorBox');
            errBox.classList.add('hidden');

            try {
                const firstName = document.getElementById('regFirstName').value;
                const lastName = document.getElementById('regLastName').value;
                const phone = document.getElementById('regPhone').value;
                const email = document.getElementById('regEmail').value;
                const password = document.getElementById('regPassword').value;
                const confirmPassword = document.getElementById('regConfirmPassword').value;
                const consent = document.getElementById('regConsent').checked;

                if (password !== confirmPassword) {
                    throw new Error('Las contraseñas no coinciden.');
                }

                // Create the user
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        email: email, 
                        password: password,
                        first_name: firstName,
                        last_name: lastName,
                        phone: phone,
                        data_protection_consent: consent
                    })
                });

                const data = await res.json();
                
                // fastapi usually returns 400 Bad Request if email exists
                if (!res.ok) {
                    throw new Error(data.detail || 'Error al completar el registro. Es posible que el correo ya exista.');
                }

                // Automatic Login after successful registration
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);
                
                const loginRes = await fetch('/api/auth/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });
                
                if (loginRes.ok) {
                    const loginData = await loginRes.json();
                    localStorage.setItem('jhire_jwt_token', loginData.access_token);
                    window.location.href = 'catalogo_usuario.html'; // Default user view
                } else {
                    alert('Registro exitoso. Inicia sesión manualmente.');
                    registerModal.classList.add('hidden');
                    registerForm.reset();
                }

            } catch (err) {
                errBox.innerText = err.message;
                errBox.classList.remove('hidden');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // Static interactivities
    document.body.addEventListener('click', (e) => {
        // Find closest button or link
        const target = e.target.closest('button, a');
        if (!target) return;

        const text = target.innerText.trim().toUpperCase();

        // Export Reports
        if (text.includes('EXPORTAR REPORTE') || text.includes('DESCARGAR EXCEL')) {
            e.preventDefault();
            Swal.fire({ toast: true, position: 'top-end', icon: 'info', title: 'Generando Excel...', showConfirmButton: false, timer: 2000 });
            window.location.href = "/api/reports/excel";
        }
        if (text.includes('DESCARGAR PDF')) {
            e.preventDefault();
            Swal.fire({ toast: true, position: 'top-end', icon: 'info', title: 'Generando PDF...', showConfirmButton: false, timer: 2000 });
            window.location.href = "/api/reports/pdf";
        }

        // AI Insights Refresh
        if (text.includes('ACTUALIZAR IA') || text.includes('REFRESH AI INSIGHTS')) {
            e.preventDefault();
            const icon = target.querySelector('.material-symbols-outlined');
            if(icon) {
                icon.classList.add('animate-spin');
                setTimeout(() => {
                    icon.classList.remove('animate-spin');
                    Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Modelos actualizados.', showConfirmButton: false, timer: 1500 });
                }, 1500);
            }
        }

        // Approve Actions from modals
        if (text.includes('APROBAR ACCIÓN')) {
            e.preventDefault();
            Swal.fire('Acción aprobada', 'El sistema registrará la orden automáticamente.', 'success');
            const modal = target.closest('div.fixed');
            if (modal) modal.style.display = 'none';
        }

        if (text.includes('DESCARTAR')) {
            e.preventDefault();
            const modal = target.closest('div.fixed');
            if (modal) modal.style.opacity = '0';
            setTimeout(() => { if(modal) modal.style.display = 'none'; }, 300);
        }

        if (text.includes('INSPECCIONAR')) {
            e.preventDefault();
            Swal.fire({ icon: 'info', title: 'Trazabilidad', text: 'Cargando log de la base de datos...' });
        }
    });

    // Create User from Dashboard
    const btnCreateUser = document.getElementById('btnCreateUser');
    const createUserModal = document.getElementById('createUserModal');
    const closeUserModal = document.getElementById('closeUserModal');
    const createUserForm = document.getElementById('createUserForm');

    if (btnCreateUser && createUserModal) {
        btnCreateUser.addEventListener('click', () => {
            createUserModal.classList.remove('pointer-events-none');
            setTimeout(() => createUserModal.classList.remove('opacity-0'), 10);
        });
        closeUserModal.addEventListener('click', () => {
             createUserModal.classList.add('opacity-0');
             setTimeout(() => createUserModal.classList.add('pointer-events-none'), 300);
        });
        
        createUserForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = createUserForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = 'Creando...';
            btn.disabled = true;
            
            const errBox = document.getElementById('createErrorBox');
            errBox.classList.add('hidden');
            
            try {
                const email = document.getElementById('newEmail').value;
                const password = document.getElementById('newPassword').value;
                
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Error al crear la cuenta del usuario');
                
                Swal.fire('Registrado', `¡El usuario ${email} ha sido registrado!`, 'success');
                createUserModal.classList.add('opacity-0');
                setTimeout(() => createUserModal.classList.add('pointer-events-none'), 300);
                createUserForm.reset();
            } catch (err) {
                errBox.innerText = err.message;
                errBox.classList.remove('hidden');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // Replace Dashboard data with dynamic API (Simulated if endpoint is down)
    const dashboardCheck = document.getElementById('total-sales');
    if (dashboardCheck) {
        // Fetch from nivel-ventas/pcv-ml to stay consistent with nivel_ventas.html
        fetch('/api/nivel-ventas/pcv-ml')
            .then(res => res.json())
            .then(nvData => {
                // Use the same VA_real_30d that nivel_ventas.html uses
                if (nvData && nvData.VA_real_30d) {
                    document.getElementById('total-sales').innerText = `S/ ${nvData.VA_real_30d.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                }
            }).catch(() => {});

        fetch('/api/dashboard/summary')
            .then(res => res.json())
            .then(data => {
                // Órdenes del Mes y Ticket Promedio
                if (data.sales_periods && data.sales_periods['30d']) {
                    const p30 = data.sales_periods['30d'];
                    const ordersEl = document.getElementById('orders-count');
                    if (ordersEl) ordersEl.innerText = p30.count;
                    const ticketEl = document.getElementById('avg-ticket');
                    if (ticketEl) ticketEl.innerText = `S/ ${p30.avg_ticket.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                }
                
                // Pronóstico Mañana KPI
                const forecastNextDay = document.getElementById('forecast-next-day');
                if (forecastNextDay) forecastNextDay.innerText = `S/ ${data.projected_next_day.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                
                const rankingBox = document.getElementById('product-ranking-list');
                if (rankingBox && data.top_products) {
                    rankingBox.innerHTML = '';
                    if (data.top_products.length === 0) {
                        rankingBox.innerHTML = '<p class="text-xs text-outline text-center py-4">Aún no hay transacciones para analizar.</p>';
                    } else {
                        const barColors = ['#003461','#4f46e5','#0891b2','#059669','#d97706','#dc2626','#7c3aed','#0d9488','#e11d48','#6366f1'];
                        data.top_products.forEach((p, index) => {
                            const pct = p.percentage || 0;
                            rankingBox.innerHTML += `
                            <div class="flex items-center gap-4 p-3 bg-surface rounded-xl hover:bg-surface-container-high transition-colors group">
                                <div class="w-10 h-10 rounded-lg ${index===0 ? 'bg-primary/20 text-primary' : 'bg-surface-container text-outline'} flex items-center justify-center font-black shrink-0">${String(index+1).padStart(2,'0')}</div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between mb-1">
                                        <p class="text-sm font-bold truncate text-on-surface">${p.name}</p>
                                        <span class="text-xs font-black ${index===0 ? 'text-primary' : 'text-outline'} ml-2 shrink-0">${pct}%</span>
                                    </div>
                                    <div class="w-full bg-surface-container-high rounded-full h-1.5 overflow-hidden">
                                        <div class="h-full rounded-full transition-all duration-700" style="width:${pct}%;background:${barColors[index % barColors.length]}"></div>
                                    </div>
                                    <p class="text-[10px] text-on-surface-variant font-medium mt-1">S/ ${p.contribution.toLocaleString('es-PE', {minimumFractionDigits: 2})}</p>
                                </div>
                            </div>`;
                        });
                    }
                }
                
                // ============================================
                // VENTAS POR PERÍODO (7d, 30d, 90d)
                // ============================================
                if (data.sales_periods) {
                    const fmt = (v) => `S/ ${v.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                    for (const [key, period] of Object.entries(data.sales_periods)) {
                        const totalEl = document.getElementById(`period-${key}-total`);
                        const countEl = document.getElementById(`period-${key}-count`);
                        const avgEl = document.getElementById(`period-${key}-avg`);
                        if (totalEl) totalEl.innerText = fmt(period.total);
                        if (countEl) countEl.innerText = `${period.count} órdenes`;
                        if (avgEl) avgEl.innerText = `Ticket: ${fmt(period.avg_ticket)}`;
                    }
                }
                
                // ============================================
                // PRECISIÓN DEL PRONÓSTICO (MAE, RMSE, MAPE + Chart)
                // ============================================
                if (data.forecast_precision) {
                    const fp = data.forecast_precision;
                    const maeEl = document.getElementById('precision-mae');
                    const rmseEl = document.getElementById('precision-rmse');
                    const mapeEl = document.getElementById('precision-mape');
                    if (maeEl) maeEl.innerText = `S/ ${fp.mae.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                    if (rmseEl) rmseEl.innerText = `S/ ${fp.rmse.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                    if (mapeEl) mapeEl.innerText = `${fp.mape}%`;
                    
                    // Render precision comparison chart
                    const precCanvas = document.getElementById('precisionChart');
                    if (precCanvas && fp.comparison && fp.comparison.length > 0) {
                        const precCtx = precCanvas.getContext('2d');
                        new Chart(precCtx, {
                            type: 'bar',
                            data: {
                                labels: fp.comparison.map(c => c.date),
                                datasets: [
                                    {
                                        label: 'Venta Real (S/)',
                                        data: fp.comparison.map(c => c.real),
                                        backgroundColor: 'rgba(0, 52, 97, 0.75)',
                                        borderColor: '#003461',
                                        borderWidth: 1,
                                        borderRadius: 4,
                                        barPercentage: 0.7
                                    },
                                    {
                                        label: 'Proyección IA (S/)',
                                        data: fp.comparison.map(c => c.predicted),
                                        backgroundColor: 'rgba(16, 185, 129, 0.55)',
                                        borderColor: '#10b981',
                                        borderWidth: 1,
                                        borderRadius: 4,
                                        borderDash: [3, 3],
                                        barPercentage: 0.7
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: { font: { family: 'Inter', size: 10, weight: 'bold' }, usePointStyle: true, pointStyleWidth: 12 }
                                    },
                                    tooltip: {
                                        callbacks: {
                                            afterBody: function(items) {
                                                const idx = items[0].dataIndex;
                                                const errPct = fp.comparison[idx].error_pct;
                                                return `Error: ${errPct}%`;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    x: {
                                        grid: { display: false },
                                        ticks: { font: { family: 'Inter', size: 10, weight: 'bold' }, color: '#727781' }
                                    },
                                    y: {
                                        beginAtZero: true,
                                        grid: { color: 'rgba(194,199,209,0.2)' },
                                        ticks: {
                                            font: { family: 'Inter', size: 10 },
                                            color: '#727781',
                                            callback: function(val) { return 'S/ ' + val.toLocaleString('es-PE'); }
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
                
                // NEW: Render Chart.js Forecast Chart
                const forecastCanvas = document.getElementById('forecastChart');
                if (forecastCanvas && data.daily_labels && data.daily_labels.length > 0) {
                    const ctx = forecastCanvas.getContext('2d');
                    
                    // Historical data (real sales)
                    const historicalData = data.daily_values;
                    const historicalLabels = data.daily_labels;
                    
                    // Forecast data (predicted next 7 days)
                    const forecastData = data.forecast_values;
                    const forecastLabels = data.forecast_labels;
                    
                    // Combined labels
                    const allLabels = [...historicalLabels, ...forecastLabels];
                    
                    // Build datasets: historical has nulls for future, forecast has nulls for past
                    // Connect them at the boundary by overlapping the last real point
                    const realDataset = [...historicalData, ...forecastLabels.map(() => null)];
                    const predDataset = [...historicalLabels.slice(0, -1).map(() => null), historicalData[historicalData.length - 1], ...forecastData];
                    
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: allLabels,
                            datasets: [
                                {
                                    label: 'Ventas Reales (S/)',
                                    data: realDataset,
                                    borderColor: '#003461',
                                    backgroundColor: 'rgba(0, 52, 97, 0.08)',
                                    borderWidth: 2.5,
                                    pointRadius: 3,
                                    pointBackgroundColor: '#003461',
                                    tension: 0.4,
                                    fill: true,
                                    spanGaps: false
                                },
                                {
                                    label: 'Pronóstico IA (S/)',
                                    data: predDataset,
                                    borderColor: '#10b981',
                                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                                    borderWidth: 2.5,
                                    borderDash: [6, 4],
                                    pointRadius: 4,
                                    pointStyle: 'triangle',
                                    pointBackgroundColor: '#10b981',
                                    tension: 0.4,
                                    fill: true,
                                    spanGaps: false
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                intersect: false,
                                mode: 'index'
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(0,0,0,0.8)',
                                    titleFont: { family: 'Inter', weight: 'bold' },
                                    bodyFont: { family: 'Inter' },
                                    padding: 12,
                                    cornerRadius: 8,
                                    callbacks: {
                                        label: function(ctx) {
                                            return ctx.dataset.label + ': S/ ' + (ctx.parsed.y ? ctx.parsed.y.toFixed(2) : '—');
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    grid: { display: false },
                                    ticks: { font: { family: 'Inter', size: 10, weight: 'bold' }, color: '#727781' }
                                },
                                y: {
                                    beginAtZero: true,
                                    grid: { color: 'rgba(194,199,209,0.2)' },
                                    ticks: {
                                        font: { family: 'Inter', size: 10 },
                                        color: '#727781',
                                        callback: function(val) { return 'S/ ' + val.toLocaleString('es-PE'); }
                                    }
                                }
                            }
                        }
                    });
                }
            })
            .catch(err => {
                console.log("Dashboard summary fetch error", err);
                if (document.getElementById('forecast-accuracy')) document.getElementById('forecast-accuracy').innerText = `--`;
            });
    }
    // Fetch Products dynamically if productGrid exists
    const productGrid = document.getElementById('productGrid');
    if (productGrid) {
        fetch('/api/products')
            .then(res => {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(products => {
                if (!Array.isArray(products)) throw new Error("Invalid response format");
                
                productGrid.innerHTML = ''; // clear loading state
                
                products.forEach(p => {
                    const priceSoles = p.price_soles.toLocaleString('es-PE', {minimumFractionDigits: 2});
                    const safeDesc = p.description || '';
                    const stockTag = p.stock > 0 
                        ? `<span class="px-2 py-0.5 rounded-full bg-tertiary/10 text-tertiary text-[10px] font-bold uppercase tracking-wider">En Stock (${p.stock})</span>`
                        : `<span class="px-2 py-0.5 rounded-full bg-error/10 text-error text-[10px] font-bold uppercase tracking-wider">Sin Stock</span>`;
                        
                    const sku = `SKU: JHIRE-${p.id.toString().padStart(4, '0')}`;
                    
                    const cardHTML = `
<!-- Product Card -->
<div class="group relative flex flex-col bg-surface dark:bg-surface-container border-l-4 border-transparent hover:border-primary transition-all overflow-hidden cursor-pointer shadow-sm hover:shadow-lg">
    <div class="h-56 w-full overflow-hidden bg-surface-container-low">
        <img class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" src="${p.image_url}" alt="${p.name}"/>
    </div>
    <div class="p-6 flex flex-col h-full">
        <div class="flex justify-between items-start mb-4">
            ${stockTag}
            <span class="text-xl font-headline font-bold text-primary">S/ ${priceSoles}</span>
        </div>
        <h3 class="text-lg font-bold text-on-surface mb-2 leading-tight">${p.name}</h3>
        <p class="text-sm text-on-surface-variant line-clamp-2 mb-6">${safeDesc}</p>
        <div class="mt-auto flex items-center justify-between border-t border-outline-variant/10 pt-4">
            <span class="text-[10px] font-label font-semibold text-on-surface-variant uppercase tracking-tighter">${sku}</span>
            <button onclick="window.location.href='detalle_producto.html?id=${p.id}'" class="flex items-center gap-2 text-primary font-bold text-sm group/btn">Ver Detalles <span class="material-symbols-outlined text-sm group-hover/btn:translate-x-1 transition-transform">arrow_forward</span></button>
        </div>
    </div>
</div>`;
                    productGrid.innerHTML += cardHTML;
                });
            })
            .catch(err => {
                console.error("Error fetching products", err);
                productGrid.innerHTML = '<p class="col-span-1 md:col-span-3 text-center text-error font-bold">Error cargando el catálogo de productos.</p>';
            });
    }

    // Dynamic Search UI Logic for Product Grid
    const searchInput = document.getElementById('searchInput');
    if (searchInput && productGrid) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const cards = productGrid.querySelectorAll('.group'); // each product card wrapper
            
            cards.forEach(card => {
                const title = card.querySelector('h3').innerText.toLowerCase();
                const desc = card.querySelector('p').innerText.toLowerCase();
                if (title.includes(term) || desc.includes(term)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Category Filtering Logic for Product Grid
    const categoryFilterContainer = document.getElementById('categoryFilterContainer');
    if (categoryFilterContainer && productGrid) {
        const filterBtns = categoryFilterContainer.querySelectorAll('button[data-category]');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // UI update
                filterBtns.forEach(b => {
                    b.classList.remove('bg-primary', 'text-on-primary', 'shadow-sm');
                    b.classList.add('text-on-surface-variant');
                });
                const cur = e.currentTarget;
                cur.classList.remove('text-on-surface-variant');
                cur.classList.add('bg-primary', 'text-on-primary', 'shadow-sm');
                
                const cat = cur.dataset.category;
                const cards = productGrid.querySelectorAll('.group');
                cards.forEach(card => {
                    const title = card.querySelector('h3').innerText.toLowerCase();
                    if (cat === 'all' || title.includes(cat)) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // Product Details Logic
    const urlParams = new URLSearchParams(window.location.search);
    const productId = urlParams.get('id');
    const productTitle = document.getElementById('productTitle');
    
    if (productId && productTitle) {
        fetch(`/api/products/${productId}`)
            .then(res => {
                if (!res.ok) throw new Error("Product fetch failed");
                return res.json();
            })
            .then(prod => {
                const bread = document.getElementById('breadcrumbTitle');
                if (bread) bread.innerText = prod.name;
                
                productTitle.innerText = prod.name;
                
                const img = document.getElementById('productImage');
                if (img) img.src = prod.image_url;
                
                const price = document.getElementById('productPrice');
                if (price) price.innerText = `S/ ${prod.price_soles.toFixed(2)}`;
                
                const sku = document.getElementById('productSku');
                if (sku) sku.innerText = `JHIRE-${prod.id.toString().padStart(4, '0')}`;
                
                const stock = document.getElementById('productStock');
                if (stock) stock.innerText = prod.stock;
                
                const desc = document.getElementById('productDescription');
                if (desc) desc.innerText = prod.description;
                
                // Setup Whatsapp and Add to Cart
                const wpBtn = document.getElementById('whatsappBtn');
                if (wpBtn) {
                    wpBtn.onclick = (e) => {
                        e.preventDefault();
                        const message = encodeURIComponent(`Tengo dudas sobre el producto ${prod.name}`);
                        window.open(`https://wa.me/51917103745?text=${message}`, '_blank');
                    };
                }

                const cartBtn = document.getElementById('addToCartBtn');
                if (cartBtn) {
                    cartBtn.onclick = () => {
                        const token = localStorage.getItem('jhire_jwt_token');
                        if (!token) {
                            Swal.fire({
                                icon: 'info',
                                title: 'Inicia Sesión',
                                text: 'Para comenzar a comprar en volumen, inicia sesión o regístrate en nuestro portal.',
                                confirmButtonColor: '#003461',
                                confirmButtonText: 'Iniciar Sesión'
                            }).then(() => {
                                window.location.href = 'login.html';
                            });
                            return;
                        }
                        
                        const qtyInput = document.getElementById('purchaseQuantity');
                        const qty = qtyInput ? parseInt(qtyInput.value) || 1 : 1;
                        const item = { id: prod.id, name: prod.name, price: prod.price_soles, image: prod.image_url, quantity: qty };
                        let currentCart = JSON.parse(localStorage.getItem('jhire_cart')) || [];
                        
                        // Start Timer if cart was empty
                        if (currentCart.length === 0) {
                            localStorage.setItem('jhire_cart_start_time', Date.now());
                        }

                        let existing = currentCart.find(i => i.id === item.id);
                        if(existing) { existing.quantity += qty; } else { currentCart.push(item); }
                        localStorage.setItem('jhire_cart', JSON.stringify(currentCart));
                        if(window.updateCartBadge) window.updateCartBadge();
                        Swal.fire({
                            toast: true,
                            position: 'top-end',
                            icon: 'success',
                            title: `¡${prod.name} agregado al carrito!`,
                            showConfirmButton: false,
                            timer: 2000
                        });
                    };
                }

                // ─── TRACK PRODUCT VIEW (Personalization Engine) ───────
                const _trackToken = localStorage.getItem('jhire_jwt_token');
                if (_trackToken) {
                    fetch('/api/recommendations/track-view', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${_trackToken}`
                        },
                        body: JSON.stringify({ product_id: parseInt(productId) })
                    }).then(r => r.json()).then(d => {
                        console.log('[JHIRE AI] Vista registrada:', d);
                    }).catch(() => {});
                }

                // ─── LOAD COMPLEMENTARY PRODUCTS ───────────────────────
                const compSection = document.getElementById('complementarySection');
                const compGrid = document.getElementById('complementaryGrid');
                if (compSection && compGrid) {
                    fetch(`/api/recommendations/complementary/${productId}`)
                        .then(r => r.json())
                        .then(items => {
                            if (!Array.isArray(items) || items.length === 0) return;

                            compGrid.innerHTML = '';
                            items.forEach((item, idx) => {
                                const priceFmt = item.price_soles.toLocaleString('es-PE', {minimumFractionDigits: 2});
                                compGrid.innerHTML += `
<div class="group bg-surface dark:bg-surface-container rounded-xl border border-outline-variant/20 overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer hover:-translate-y-1" onclick="window.location.href='detalle_producto.html?id=${item.id}'" style="opacity:0; animation: fadeSlideUp 0.5s ease ${idx * 0.1}s forwards;">
    <div class="h-40 overflow-hidden bg-surface-container-low">
        <img class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" src="${item.image_url}" alt="${item.name}"/>
    </div>
    <div class="p-4">
        <p class="text-[9px] font-bold uppercase tracking-widest text-primary/60 mb-1 flex items-center gap-1">
            <span class="material-symbols-outlined text-[11px]">link</span> ${item.reason}
        </p>
        <h4 class="text-sm font-bold text-on-surface mb-2 line-clamp-2 leading-snug">${item.name}</h4>
        <div class="flex items-center justify-between">
            <span class="text-lg font-extrabold text-primary">S/ ${priceFmt}</span>
            <span class="material-symbols-outlined text-primary text-sm group-hover:translate-x-1 transition-transform">arrow_forward</span>
        </div>
    </div>
</div>`;
                            });

                            compSection.classList.remove('hidden');
                            requestAnimationFrame(() => {
                                compSection.style.opacity = '1';
                                compSection.style.transform = 'translateY(0)';
                            });
                        }).catch(e => console.warn('[JHIRE] Complementary load error:', e));
                }
            });
    }

    // ─── PERSONALIZED RECOMMENDATIONS (Catalog Page) ───────────
    const _recSection = document.getElementById('personalizedSection');
    const _recGrid = document.getElementById('recommendedGrid');
    if (_recSection && _recGrid && productGrid) {
        const _recToken = localStorage.getItem('jhire_jwt_token');
        if (_recToken) {
            fetch('/api/recommendations/for-me', {
                headers: { 'Authorization': `Bearer ${_recToken}` }
            })
            .then(r => { if (!r.ok) throw new Error('Not auth'); return r.json(); })
            .then(data => {
                if (!data.recommended || data.recommended.length === 0) return;

                // Show section with animation
                _recSection.classList.remove('hidden');
                requestAnimationFrame(() => {
                    _recSection.style.opacity = '1';
                    _recSection.style.transform = 'translateY(0)';
                });

                // Profile badge
                const badge = document.getElementById('profileBadgeText');
                const badgeContainer = document.getElementById('userProfileBadge');
                if (badge && data.user_profile) {
                    const prof = data.user_profile;
                    const parts = [];
                    if (prof.unique_products_viewed > 0) parts.push(`${prof.unique_products_viewed} productos vistos`);
                    if (prof.total_orders > 0) parts.push(`${prof.total_orders} compras`);
                    if (prof.favorite_category) parts.push(`Fan de ${prof.favorite_category}s`);
                    badge.innerText = parts.join(' · ') || 'Personalizado para ti';
                    if (badgeContainer) badgeContainer.classList.remove('hidden');
                }

                // Render recommended cards (top 4)
                _recGrid.innerHTML = '';
                const topRecs = data.recommended.slice(0, 4);
                topRecs.forEach((rec, idx) => {
                    const priceFmt = rec.price_soles.toLocaleString('es-PE', {minimumFractionDigits: 2});
                    const hasDiscount = rec.discount_pct > 0;
                    const discPriceFmt = hasDiscount ? rec.discounted_price.toLocaleString('es-PE', {minimumFractionDigits: 2}) : '';

                    const discountBadge = hasDiscount ? `
                        <div class="absolute top-3 right-3 z-10 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-[10px] font-black px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 animate-pulse">
                            <span class="material-symbols-outlined text-[12px]">local_offer</span> -${rec.discount_pct}%
                        </div>` : '';

                    const priceBlock = hasDiscount ? `
                        <div class="flex items-baseline gap-2">
                            <span class="text-xl font-extrabold text-primary">S/ ${discPriceFmt}</span>
                            <span class="text-sm text-outline line-through">S/ ${priceFmt}</span>
                        </div>` : `
                        <span class="text-xl font-extrabold text-primary">S/ ${priceFmt}</span>`;

                    const scoreBar = `
                        <div class="mt-2 flex items-center gap-2">
                            <div class="flex-1 h-1.5 bg-surface-container-high rounded-full overflow-hidden">
                                <div class="h-full bg-gradient-to-r from-primary to-primary/60 rounded-full transition-all duration-1000" style="width: ${rec.score}%"></div>
                            </div>
                            <span class="text-[9px] font-bold text-outline">${rec.score}%</span>
                        </div>`;

                    _recGrid.innerHTML += `
<div class="group relative bg-surface dark:bg-surface-container rounded-xl border border-outline-variant/20 overflow-hidden shadow-sm hover:shadow-2xl transition-all duration-300 cursor-pointer hover:-translate-y-1" onclick="window.location.href='detalle_producto.html?id=${rec.id}'" style="opacity:0; animation: fadeSlideUp 0.5s ease ${idx * 0.12}s forwards;">
    ${discountBadge}
    <div class="h-48 overflow-hidden bg-surface-container-low relative">
        <img class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" src="${rec.image_url}" alt="${rec.name}"/>
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/40 to-transparent h-16"></div>
    </div>
    <div class="p-5">
        <p class="text-[9px] font-bold uppercase tracking-widest text-primary/70 mb-1.5 flex items-center gap-1">
            <span class="material-symbols-outlined text-[11px]" style="font-variation-settings: 'FILL' 1;">auto_awesome</span> ${rec.reason}
        </p>
        <h4 class="text-sm font-bold text-on-surface mb-3 line-clamp-2 leading-snug">${rec.name}</h4>
        ${priceBlock}
        ${hasDiscount ? `<span class="inline-block mt-1 text-[9px] font-bold text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 rounded-full">${rec.discount_label}</span>` : ''}
        ${scoreBar}
    </div>
</div>`;
                });

                // Render discount banner
                if (data.personal_discounts && data.personal_discounts.length > 0) {
                    const discBanner = document.getElementById('personalDiscountBanner');
                    const discList = document.getElementById('personalDiscountsList');
                    if (discBanner && discList) {
                        discBanner.classList.remove('hidden');
                        discList.innerHTML = '';
                        data.personal_discounts.slice(0, 3).forEach(disc => {
                            const origFmt = disc.original_price.toLocaleString('es-PE', {minimumFractionDigits: 2});
                            const discFmt = disc.discounted_price.toLocaleString('es-PE', {minimumFractionDigits: 2});
                            discList.innerHTML += `
<div class="bg-white dark:bg-surface-container rounded-xl p-4 border border-amber-200/50 dark:border-amber-700/30 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer" onclick="window.location.href='detalle_producto.html?id=${disc.product_id}'">
    <img class="w-14 h-14 rounded-lg object-cover border border-outline-variant/20" src="${disc.image_url}" alt="${disc.product_name}"/>
    <div class="flex-1 min-w-0">
        <p class="text-xs font-bold text-on-surface truncate">${disc.product_name}</p>
        <div class="flex items-baseline gap-2 mt-1">
            <span class="text-base font-extrabold text-amber-700 dark:text-amber-400">S/ ${discFmt}</span>
            <span class="text-xs text-outline line-through">S/ ${origFmt}</span>
        </div>
        <span class="inline-flex items-center gap-1 mt-1 text-[9px] font-bold text-white bg-gradient-to-r from-amber-500 to-orange-500 px-2 py-0.5 rounded-full">
            <span class="material-symbols-outlined text-[10px]">local_offer</span> -${disc.discount_pct}% ${disc.discount_label}
        </span>
    </div>
</div>`;
                        });
                    }
                }
            }).catch(e => console.log('[JHIRE] Recommendations not available (user may not be logged in):', e.message));
        }
    }

    // --- AI Chatbot Widget Logic ---
    // Only render if we are authenticated (have a token) and NOT on an admin page
    if (localStorage.getItem('jhire_jwt_token') && !window.location.pathname.includes('dashboard.html') && !window.location.pathname.includes('admin') && !window.location.pathname.includes('inventario.html')) {
        const chatWidgetHTML = `
        <div class="fixed bottom-8 right-8 z-50 flex flex-col items-end gap-4" id="aiChatContainer">
            <!-- Chat Bubble -->
            <div id="aiChatWindow" class="w-80 bg-surface dark:bg-surface-container rounded-xl shadow-2xl border border-outline-variant/30 overflow-hidden flex flex-col opacity-0 pointer-events-none translate-y-4 transition-all duration-300">
                <div class="bg-primary p-4 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-tertiary-fixed flex items-center justify-center">
                            <span class="material-symbols-outlined text-on-tertiary-fixed text-sm" style="font-variation-settings: 'FILL' 1;">smart_toy</span>
                        </div>
                        <div>
                            <h4 class="text-sm font-bold text-on-primary">JHIRE AI</h4>
                            <p class="text-[10px] text-on-primary-container">Asistente Local</p>
                        </div>
                    </div>
                    <button id="closeAiChatBtn" class="text-on-primary/60 hover:text-on-primary">
                        <span class="material-symbols-outlined text-lg">close</span>
                    </button>
                </div>
                
                <div id="aiChatMessages" class="h-64 p-4 overflow-y-auto flex flex-col gap-4 bg-surface text-sm">
                    <div class="self-start bg-surface-container-high p-3 rounded-lg rounded-tl-none max-w-[85%] text-on-surface">
                        ¡Hola! Soy tu asistente inteligente local. Pregúntame sobre productos, precios o recomendaciones de nuestro catálogo.
                    </div>
                </div>
                
                <form id="aiChatForm" class="p-3 border-t border-outline-variant/20 bg-white">
                    <div class="flex items-center gap-2 bg-surface-container-low px-3 py-2 rounded-sm border-b border-outline">
                        <input id="aiChatInput" class="bg-transparent border-none text-xs flex-1 focus:ring-0" placeholder="Escribe un mensaje..." type="text" autocomplete="off" required/>
                        <button type="submit" id="aiChatSubmitBtn" class="text-primary disabled:opacity-50">
                            <span class="material-symbols-outlined text-lg">send</span>
                        </button>
                    </div>
                </form>
            </div>
            
            <!-- Floating Action Button -->
            <button id="aiChatToggleBtn" class="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-primary-container text-on-primary flex items-center justify-center shadow-lg hover:shadow-primary/40 hover:-translate-y-1 transition-all">
                <span class="material-symbols-outlined text-2xl" id="aiChatIcon" style="font-variation-settings: 'FILL' 1;">chat_bubble</span>
            </button>
        </div>`;

        const isAdminPage = ['dashboard', 'inventario', 'ventas', 'crm', 'facturacion', 'admin_'].some(p => window.location.pathname.includes(p));
        if (!isAdminPage) {
            document.body.insertAdjacentHTML('beforeend', chatWidgetHTML);

            const chatWindow = document.getElementById('aiChatWindow');
        const chatToggleBtn = document.getElementById('aiChatToggleBtn');
        const closeAiChatBtn = document.getElementById('closeAiChatBtn');
        const chatForm = document.getElementById('aiChatForm');
        const chatInput = document.getElementById('aiChatInput');
        const chatMessages = document.getElementById('aiChatMessages');
        const chatSubmitBtn = document.getElementById('aiChatSubmitBtn');
        const chatIcon = document.getElementById('aiChatIcon');

        let chatOpen = false;

        const toggleChat = () => {
            chatOpen = !chatOpen;
            if (chatOpen) {
                chatWindow.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-4');
                chatIcon.innerText = "close";
                setTimeout(() => chatInput.focus(), 300);
            } else {
                chatWindow.classList.add('opacity-0', 'pointer-events-none', 'translate-y-4');
                chatIcon.innerText = "chat_bubble";
            }
        };

        chatToggleBtn.addEventListener('click', toggleChat);
        closeAiChatBtn.addEventListener('click', toggleChat);

        const appendMessage = (text, isUser = false) => {
            const wrapper = document.createElement('div');
            if (isUser) {
                wrapper.className = "self-end bg-primary p-3 rounded-lg rounded-tr-none max-w-[85%] text-on-primary";
            } else {
                wrapper.className = "self-start bg-surface-container-high p-3 rounded-lg rounded-tl-none max-w-[85%] text-on-surface";
            }
            wrapper.innerText = text;
            chatMessages.appendChild(wrapper);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            appendMessage(message, true);
            chatInput.value = '';
            chatInput.disabled = true;
            chatSubmitBtn.disabled = true;

            // Loading state
            const loadingMsgId = "loading-" + Date.now();
            const loadingHTML = `<div id="${loadingMsgId}" class="self-start text-xs text-on-surface-variant flex gap-1 items-center animate-pulse"><span class="material-symbols-outlined text-[14px]">smart_toy</span> Pensando...</div>`;
            chatMessages.insertAdjacentHTML('beforeend', loadingHTML);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/api/chat/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                document.getElementById(loadingMsgId).remove();

                if (!response.ok) throw new Error(data.detail || "Error en el servidor");
                
                appendMessage(data.response, false);
            } catch (err) {
                console.error(err);
                document.getElementById(loadingMsgId).remove();
                appendMessage("El servidor de Inteligencia Artificial está procesando o desconectado. Por favor, revisa la terminal del backend e inténtalo luego.", false);
            } finally {
                chatInput.disabled = false;
                chatSubmitBtn.disabled = false;
                chatInput.focus();
            }
        });
        } // End of if(!isAdminPage)
    }

    // --- System Shopping Cart Logic ---
    const headerActions = document.querySelector('nav .flex.items-center.gap-6 > .flex.items-center.gap-4.relative');
    if (headerActions) {
        const cartIconHtml = `
        <div class="relative cursor-pointer text-on-surface hover:text-primary transition-colors flex items-center justify-center p-2 rounded-full hover:bg-primary/5" id="navCartBtn" title="Ver Carrito">
            <span class="material-symbols-outlined text-2xl">shopping_cart</span>
            <span id="cartBadge" class="absolute top-0 right-0 bg-error text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full hidden">0</span>
        </div>
        `;
        headerActions.insertAdjacentHTML('afterbegin', cartIconHtml);
    }

    const cartModalHtml = `
    <div id="cartModal" class="hidden fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-white dark:bg-surface-container rounded-2xl p-6 w-full max-w-md shadow-2xl relative flex flex-col max-h-[85vh]">
            <button id="closeCartModal" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white bg-surface-container-low dark:bg-surface rounded-full w-8 h-8 flex items-center justify-center">
                <span class="material-symbols-outlined text-sm">close</span>
            </button>
            <h3 class="text-2xl font-headline font-extrabold text-primary mb-6 flex items-center gap-2"><span class="material-symbols-outlined text-primary">shopping_cart</span> Tu Carrito</h3>
            <div id="cartItemsList" class="flex-1 overflow-y-auto space-y-3 mb-6 bg-surface dark:bg-surface-container dark:bg-surface border rounded-xl p-2 border-outline-variant/20 dark:border-white/5 shadow-inner">
                <!-- Items list dynamic -->
            </div>
            <!-- ML RECOMMENDATIONS -->
            <div id="cartAiRecommendations" class="hidden mb-4">
                <p class="text-[10px] font-black uppercase tracking-widest text-primary flex items-center gap-1 mb-2"><span class="material-symbols-outlined text-[12px]">auto_awesome</span> IA Recomienda para acompañar</p>
                <div id="cartAiRecsList" class="flex gap-2 overflow-x-auto pb-2">
                    <!-- Dynamic Recs -->
                </div>
            </div>
            <div class="border-t pt-4 border-outline-variant/20 dark:border-white/10 space-y-4">
                <div class="flex justify-between font-black text-xl text-on-surface">
                    <span>TOTAL:</span>
                    <span id="cartTotal">S/ 0.00</span>
                </div>
                <button id="cartCheckoutBtn" class="w-full py-4 bg-gradient-to-br from-primary to-primary-container text-white rounded-xl font-bold hover:shadow-xl hover:-translate-y-1 transition-all text-sm tracking-wide">CONFIRMAR PEDIDO Y PAGAR</button>
                <div class="text-center">
                    <button id="cartClearBtn" class="text-error text-xs font-bold hover:underline opacity-80 hover:opacity-100 uppercase tracking-widest"><span class="material-symbols-outlined text-[10px] align-middle">delete</span> Vaciar Carrito</button>
                </div>
            </div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', cartModalHtml);

    const checkCartState = () => JSON.parse(localStorage.getItem('jhire_cart')) || [];
    
    window.updateCartBadge = () => {
        const badge = document.getElementById('cartBadge');
        if(!badge) return;
        const currentData = checkCartState();
        let totalCount = 0;
        currentData.forEach(i => totalCount += (i.quantity || 1));
        if(totalCount > 0) {
            badge.innerText = totalCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    };
    
    window.changeCartQuantity = (id, delta) => {
        let currentCart = checkCartState();
        
        // Start Timer for TPRCP if cart was empty
        if (currentCart.length === 0 && delta > 0) {
            localStorage.setItem('jhire_cart_start_time', Date.now());
        }

        let item = currentCart.find(i => i.id === id);
        if(item) {
            item.quantity = (item.quantity || 1) + delta;
            if(item.quantity <= 0) currentCart = currentCart.filter(i => i.id !== id);
            localStorage.setItem('jhire_cart', JSON.stringify(currentCart));
            window.updateCartBadge();
            renderCartItems();
        } else if (delta > 0) {
            // Wait, this function might just change quantity. Where do they add a NEW item to the cart?
            // Actually, if it's not in the cart, how is it added? We need to look at `addToCart` if it exists.
        }
    };
    
    // Initial UI Setup for Cart
    window.updateCartBadge();

    const renderCartItems = () => {
        const list = document.getElementById('cartItemsList');
        const cartTotal = document.getElementById('cartTotal');
        const data = checkCartState();
        list.innerHTML = '';
        let total = 0;
        
        if (data.length === 0) {
            list.innerHTML = '<div class="h-40 flex flex-col items-center justify-center text-outline-variant"><span class="material-symbols-outlined text-4xl mb-2 opacity-50">shopping_cart</span><p class="text-sm font-bold">Tu carrito está vacío.</p></div>';
        } else {
            data.forEach((item) => {
                const qty = item.quantity || 1;
                const subT = item.price * qty;
                total += subT;
                list.insertAdjacentHTML('beforeend', `
                    <div class="flex items-center gap-3 bg-white dark:bg-surface-container-low p-3 rounded-lg border border-outline-variant/10 shadow-sm relative">
                        <img src="${item.image}" class="w-12 h-12 object-contain rounded bg-surface p-1">
                        <div class="flex-1 min-w-0 pr-16">
                            <p class="text-[11px] font-bold text-on-surface leading-tight truncate">${item.name}</p>
                            <p class="text-xs text-primary font-black mt-1">S/ ${item.price.toFixed(2)} c/u</p>
                        </div>
                        <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 bg-surface-container-low dark:bg-surface-container-high rounded-md px-1 py-1 border border-outline/10">
                            <button onclick="window.changeCartQuantity(${item.id}, -1)" class="w-5 h-5 flex items-center justify-center bg-white dark:bg-surface-container rounded shadow-sm text-on-surface font-bold hover:bg-surface-container-highest transition-colors">-</button>
                            <span class="text-xs font-black w-4 text-center">${qty}</span>
                            <button onclick="window.changeCartQuantity(${item.id}, 1)" class="w-5 h-5 flex items-center justify-center bg-white dark:bg-surface-container rounded shadow-sm text-on-surface font-bold hover:bg-surface-container-highest transition-colors">+</button>
                        </div>
                    </div>
                `);
            });
        }
        cartTotal.innerText = `S/ ${total.toFixed(2)}`;
        
        // Fetch ML Recommendations
        const aiContainer = document.getElementById('cartAiRecommendations');
        const aiList = document.getElementById('cartAiRecsList');
        if (data.length > 0 && aiContainer && aiList) {
            const productIds = data.map(i => i.id);
            fetch('/api/orders/recommend-products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_product_ids: productIds })
            }).then(r => r.json()).then(res => {
                if (res.recommendations && res.recommendations.length > 0) {
                    aiContainer.classList.remove('hidden');
                    aiList.innerHTML = res.recommendations.map(r => `
                        <div class="shrink-0 w-40 bg-surface-container-low border border-outline-variant/20 rounded-lg p-2 flex flex-col gap-1 shadow-sm relative">
                            <button onclick="window.addRecToCart(${r.id}, '${r.name}', ${r.price_soles}, '${r.image_url}')" class="absolute -top-2 -right-2 bg-primary text-white w-6 h-6 rounded-full flex items-center justify-center shadow-md hover:scale-110 transition-transform">
                                <span class="material-symbols-outlined text-[12px]">add</span>
                            </button>
                            <img src="${r.image_url}" class="w-full h-12 object-contain rounded bg-white p-1">
                            <p class="text-[9px] font-bold text-on-surface line-clamp-1">${r.name}</p>
                            <p class="text-[10px] font-black text-primary">S/ ${r.price_soles.toFixed(2)}</p>
                        </div>
                    `).join('');
                } else {
                    aiContainer.classList.add('hidden');
                }
            }).catch(e => {
                aiContainer.classList.add('hidden');
            });
        } else if (aiContainer) {
            aiContainer.classList.add('hidden');
        }
    };
    
    window.addRecToCart = (id, name, price, image) => {
        let currentCart = checkCartState();
        currentCart.push({ id, name, price, image, quantity: 1 });
        localStorage.setItem('jhire_cart', JSON.stringify(currentCart));
        window.updateCartBadge();
        renderCartItems();
    };

    document.getElementById('navCartBtn')?.addEventListener('click', () => {
        renderCartItems();
        document.getElementById('cartModal').classList.remove('hidden');
    });
    document.getElementById('closeCartModal')?.addEventListener('click', () => {
        document.getElementById('cartModal').classList.add('hidden');
    });
    document.getElementById('cartClearBtn')?.addEventListener('click', () => {
        localStorage.setItem('jhire_cart', JSON.stringify([]));
        window.updateCartBadge();
        renderCartItems();
    });
    document.getElementById('cartCheckoutBtn')?.addEventListener('click', async () => {
        const data = checkCartState();
        if(data.length === 0) return Swal.fire('Oops', 'No hay productos en tu carrito para procesar una compra.', 'error');
        
        const token = localStorage.getItem('jhire_jwt_token');
        const originalBtnText = document.getElementById('cartCheckoutBtn').innerText;
        document.getElementById('cartCheckoutBtn').innerText = 'PROCESANDO...';
        
        try {
            // Get registration time TPRCP
            const startTime = localStorage.getItem('jhire_cart_start_time');
            let regTimeSeconds = 0;
            if (startTime) {
                regTimeSeconds = Math.floor((Date.now() - parseInt(startTime)) / 1000);
            }

            const bodyPayload = { 
                items: data.map(i => ({ product_id: i.id, quantity: i.quantity || 1 })),
                registration_time_seconds: regTimeSeconds
            };
            
            const res = await fetch('/api/orders/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(bodyPayload)
            });
            if(!res.ok) throw new Error("Error creando orden " + await res.text());
            
            const orderRes = await res.json();
            
            // Build Whatsapp Text
            let message = `*NUEVO PEDIDO JHIRE (#ORD-${orderRes.id})*\nHola, confirmo esta compra corporativa:\n\n`;
            data.forEach(i => {
                message += `- ${i.quantity || 1}x ${i.name.trim()} (S/ ${i.price.toFixed(2)} c/u)\n`;
            });
            message += `\n*TOTAL FINAL: S/ ${orderRes.total_price.toFixed(2)}*\n\nPor favor, confirmad el procesamiento operativo.`;
            
            window.open(`https://wa.me/51917103745?text=${encodeURIComponent(message)}`, '_blank');
            
            localStorage.setItem('jhire_cart', JSON.stringify([]));
            window.updateCartBadge();
            document.getElementById('cartModal').classList.add('hidden');
            window.location.href = 'mis_pedidos.html';
            
        } catch (error) {
            console.error(error);
            Swal.fire('Error', 'Problema procesando la compra, revisa conexión con el servidor.', 'error');
            document.getElementById('cartCheckoutBtn').innerText = originalBtnText;
        }
    });

    // --- Mis Pedidos Logic ---
    if(window.location.pathname.includes('mis_pedidos.html')) {
        const token = localStorage.getItem('jhire_jwt_token');
        if(token) {
            fetch('/api/orders/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(async r => {
                if(!r.ok) {
                    const err = await r.json();
                    throw new Error(err.detail || "Error loading orders");
                }
                return r.json();
            }).then(orders => {
                const list = document.getElementById('ordersList');
                if(!list) return;
                
                list.innerHTML = '';
                if(!orders || orders.length === 0) {
                    list.innerHTML = '<p class="text-center text-outline-variant font-bold py-16">No tienes historial de pedidos todavía.</p>';
                } else {
                    orders.forEach(order => {
                        let statusColor = "bg-primary-container text-on-primary-container";
                        let timerDiv = '';
                        if(order.status === 'En Proceso') { statusColor = "bg-warning-container text-warning font-bold animate-pulse"; }
                        if(order.status === 'Completado') { statusColor = "bg-success-container text-success font-bold"; }
                        if(order.status === 'Cancelado' || order.status === 'Rechazado') { statusColor = "bg-error-container text-error font-bold"; }
                        
                        let itemsHtml = order.items.map(i => `<li class="text-sm font-medium text-on-surface-variant flex gap-2"><span>${i.quantity}x</span> <span class="truncate">${i.product.name}</span></li>`).join('');
                        
                        // Timers
                        if(order.status === 'En Proceso') {
                            timerDiv = `<div class="mt-4 pt-4 border-t border-outline/10"><p class="text-[10px] font-bold text-outline uppercase tracking-widest mb-1 shadow-sm">Tiempo límite operativo:</p><div class="tracking-tighter font-headline text-2xl font-black text-error countdown-timer" data-start="${order.created_at}">--:--:--</div></div>`;
                        }

                        list.insertAdjacentHTML('beforeend', `
                            <div class="bg-white dark:bg-surface-container rounded-2xl shadow-sm border border-outline/10 dark:border-white/5 p-6 md:p-8 flex flex-col md:flex-row justify-between md:items-center gap-6 group hover:shadow-lg transition-all">
                                <div>
                                    <div class="flex items-center gap-3 mb-2">
                                        <h3 class="text-xl font-bold font-headline text-on-surface">Orden #ORD-${order.id}</h3>
                                        <span class="px-3 py-1 rounded-full text-[10px] uppercase tracking-widest ${statusColor}">${order.status}</span>
                                    </div>
                                    <p class="text-xs text-outline mb-4">Creada el: ${new Date(order.created_at).toLocaleString()}</p>
                                    <ul class="list-disc list-inside space-y-1 mb-2">
                                        ${itemsHtml}
                                    </ul>
                                </div>
                                <div class="text-right shrink-0">
                                    <p class="text-[10px] text-outline font-bold uppercase tracking-widest">Total Abonado</p>
                                    <p class="text-3xl font-black text-primary tracking-tighter">S/ ${order.total_price.toFixed(2)}</p>
                                    ${timerDiv}
                                </div>
                            </div>
                        `);
                    });
                    
                    // Activate live timers
                    setInterval(() => {
                        document.querySelectorAll('.countdown-timer').forEach(el => {
                            let createdObj = new Date(el.getAttribute('data-start') + 'Z'); 
                            let target = createdObj.getTime() + (72 * 3600 * 1000); 
                            let now = new Date().getTime();
                            let rem = target - now;
                            if(rem > 0) {
                                let h = Math.floor((rem % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)) + Math.floor(rem / (1000 * 60 * 60 * 24)) * 24;
                                let m = Math.floor((rem % (1000 * 60 * 60)) / (1000 * 60));
                                let s = Math.floor((rem % (1000 * 60)) / 1000);
                                el.innerText = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
                            } else {
                                el.innerText = "00:00:00 (CERRADO)";
                                el.classList.remove('text-error');
                                el.classList.add('text-outline');
                            }
                        });
                    }, 1000);
                }
            }).catch(err => {
                console.error(err);
                const list = document.getElementById('ordersList');
                if(list) list.innerHTML = '<p class="text-center text-error font-bold py-16">Ocurrió un problema cargando tus pedidos. Inicia sesión nuevamente.</p>';
            });
        } else {
            const list = document.getElementById('ordersList');
            if(list) list.innerHTML = '<p class="text-center text-outline-variant font-bold py-16">Inicia sesión para ver tu historial de comandos.</p>';
        }
    }
    // --- Dashboard Admin Logic ---
    if(window.location.pathname.includes('dashboard.html')) {
        const token = localStorage.getItem('jhire_jwt_token');
        
        // Track when each order was first shown to admin for TPRVP measurement
        window._orderViewTimes = window._orderViewTimes || {};
        
        window.updateOrderStatus = async (orderId, newStatus) => {
            const result = await Swal.fire({
                title: '¿Estás seguro?',
                text: `¿Marcar la orden #ORD-${orderId} como ${newStatus}?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#003461',
                cancelButtonColor: '#ba1a1a',
                confirmButtonText: 'Sí, cambiar',
                cancelButtonText: 'Cancelar'
            });
            if(!result.isConfirmed) return;
            try {
                // Calculate elapsed seconds since order was displayed
                let confirmationSeconds = 0;
                if(newStatus === 'Completado' && window._orderViewTimes[orderId]) {
                    confirmationSeconds = Math.round((Date.now() - window._orderViewTimes[orderId]) / 1000);
                    if(confirmationSeconds < 1) confirmationSeconds = 1;
                }
                
                const res = await fetch(`/api/orders/${orderId}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ status: newStatus, sale_confirmation_seconds: confirmationSeconds })
                });
                if(!res.ok) throw new Error("Error status");
                delete window._orderViewTimes[orderId];
                loadAdminOrders();
            } catch(e) {
                console.error(e);
                Swal.fire('Error', 'Error al actualizar la orden.', 'error');
            }
        };

        const loadAdminOrders = async () => {
            if(!document.getElementById('adminOrdersTableBody')) return;
            try {
                const res = await fetch('/api/orders/admin', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if(res.status === 403) {
                    document.getElementById('adminOrdersTableBody').innerHTML = '<tr><td colspan="6" class="p-8 text-center text-outline text-xs text-error">Sin permisos de administrador.</td></tr>';
                    return;
                }
                const orders = await res.json();
                const tbody = document.getElementById('adminOrdersTableBody');
                tbody.innerHTML = '';
                
                if(orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-outline text-xs">No hay órdenes pendientes en este momento.</td></tr>';
                } else {
                    orders.forEach(order => {
                        // Register view time for TPRVP tracking
                        if(!window._orderViewTimes[order.id]) {
                            window._orderViewTimes[order.id] = Date.now();
                        }
                        let itemsHtml = order.items.map(i => `${i.quantity}x ${i.product.name}`).join('<br>');
                        
                        let anomalyTag = order.status === 'Anomalía / Revisión' ? '<div class="mt-1.5 inline-flex items-center gap-1 bg-error text-white px-2 py-0.5 rounded text-[9px] font-black tracking-widest animate-pulse shadow-sm"><span class="material-symbols-outlined text-[10px]">warning</span> ANOMALÍA DETECTADA</div>' : '';
                        
                        // Check if SLA expired (72h = 259200000ms)
                        let createdTime = new Date(order.created_at + 'Z').getTime();
                        let slaDeadline = createdTime + (72 * 3600 * 1000);
                        let isExpired = Date.now() > slaDeadline;
                        
                        let actionButtons = isExpired 
                            ? `<span class="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded text-[10px] font-black tracking-wider"><span class="material-symbols-outlined text-[12px]">block</span> SLA VENCIDO</span>`
                            : `<button onclick="updateOrderStatus(${order.id}, 'Completado')" class="flex-1 max-w-[90px] justify-center p-1.5 px-3 bg-success/10 hover:bg-success text-success hover:text-white rounded text-[10px] font-black tracking-wider transition-colors">ACEPTAR</button>
                               <button onclick="updateOrderStatus(${order.id}, 'Rechazado')" class="flex-1 max-w-[90px] justify-center p-1.5 px-3 bg-error/10 hover:bg-error text-error hover:text-white rounded text-[10px] font-black tracking-wider transition-colors">RECHAZAR</button>`;
                        
                        tbody.insertAdjacentHTML('beforeend', `
                            <tr class="hover:bg-surface-container-high transition-colors border-b border-outline/10 last:border-0 relative ${isExpired ? 'opacity-60' : ''}">
                                <td class="px-4 py-4 font-bold text-on-surface text-sm">#ORD-${order.id}</td>
                                <td class="px-4 py-4">
                                    <div class="text-xs font-bold text-primary">${order.user?.email || 'N/A'}</div>
                                    <div class="text-[9px] text-outline leading-tight mt-1 max-w-[200px]">${itemsHtml}</div>
                                    ${anomalyTag}
                                </td>
                                <td class="px-4 py-4 text-sm font-black text-on-surface font-headline border-r border-outline-variant/20">S/ ${order.total_price.toFixed(2)}</td>
                                <td class="px-4 py-4 text-xs font-bold ${isExpired ? 'text-gray-400' : 'text-error'} admin-timer" data-start="${order.created_at}">${isExpired ? 'EXPIRADA' : '--:--:--'}</td>
                                <td class="px-4 py-4 text-right">
                                    <div class="flex justify-end gap-2">
                                        ${actionButtons}
                                    </div>
                                </td>
                            </tr>
                        `);
                    });
                }
            } catch(e) {
                console.error(e);
            }
        };
        
    // Initialize Admin Orders if element exists
    if(document.getElementById('adminOrdersTableBody')) {
        loadAdminOrders();
        setInterval(loadAdminOrders, 15000); // Poll every 15s
        
        document.getElementById('refreshAdminOrdersBtn')?.addEventListener('click', loadAdminOrders);
        
        // Dashboard Search Bar - filters orders table
        const dashboardSearch = document.getElementById('dashboardSearchInput');
        if(dashboardSearch) {
            dashboardSearch.addEventListener('keyup', (e) => {
                const term = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#adminOrdersTableBody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(term) ? '' : 'none';
                });
            });
        }
        
        // History Search
        const historySearch = document.getElementById('historySearchInput');
        if(historySearch) {
            historySearch.addEventListener('keyup', (e) => {
                const term = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#historyTableBody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(term) ? '' : 'none';
                });
            });
        }
        
        setInterval(() => {
            document.querySelectorAll('.admin-timer').forEach(el => {
                let createdObj = new Date(el.getAttribute('data-start') + 'Z'); 
                let target = createdObj.getTime() + (72 * 3600 * 1000); 
                let now = new Date().getTime();
                let rem = target - now;
                if(rem > 0) {
                    let h = Math.floor((rem % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)) + Math.floor(rem / (1000 * 60 * 60 * 24)) * 24;
                    let m = Math.floor((rem % (1000 * 60 * 60)) / (1000 * 60));
                    let s = Math.floor((rem % (1000 * 60)) / 1000);
                    el.innerText = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
                } else {
                    el.innerText = "EXPIRADA";
                }
            });
        }, 1000);
        
        // --- WebSockets Real-Time ---
        try {
            const wsUrl = window.location.protocol === 'https:' ? 'wss://' : 'ws://' + window.location.host + '/api/dashboard/ws';
            const dashboardWs = new WebSocket(wsUrl);
            dashboardWs.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.event === "refresh_dashboard") {
                    console.log("WebSocket Ping: Refrescando métricas en tiempo real...");
                    // Flash effect to show real-time update
                    const totalSalesEl = document.getElementById('total-sales');
                    if(totalSalesEl) {
                        totalSalesEl.classList.add('text-success', 'scale-110');
                        setTimeout(() => totalSalesEl.classList.remove('text-success', 'scale-110'), 500);
                    }
                    if(typeof loadDashboardSummary === 'function') loadDashboardSummary();
                    if(typeof loadAdminOrders === 'function') loadAdminOrders();
                    if(typeof loadHistoryAdminOrders === 'function' && !document.getElementById('historyModal').classList.contains('hidden')) {
                        loadHistoryAdminOrders();
                    }
                }
            };
        } catch(e) {
            console.error("No se pudo establecer WebSocket", e);
        }
    }
    } // End of dashboard.html check
});

// Admin All Orders Fetcher
async function loadHistoryAdminOrders() {
    const tbody = document.getElementById('historyTableBody');
    if(!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="5" class="p-8 text-center text-outline text-xs">Cargando historial...</td></tr>';
    
    try {
        const token = localStorage.getItem('jhire_jwt_token');
        const res = await fetch('/api/orders/admin/all', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if(!res.ok) throw new Error('Error fetcheando historial');
        const orders = await res.json();
        
        if(orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-outline-variant text-xs">No hay historial de órdenes registrado.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = orders.map(order => {
            let statusColor = "bg-surface-container-high text-on-surface-variant"; // Default: Cancelado / En Proceso
            if(order.status === "Aprobado" || order.status === "Completado") {
                statusColor = "bg-primary-fixed text-primary font-bold";
            } else if(order.status === "Rechazado") {
                statusColor = "bg-error-container text-on-error-container font-bold";
            } else if(order.status === "Cancelado") {
                statusColor = "bg-surface-dim opacity-50";
            }
            
            return `
                <tr class="hover:bg-surface-container-high transition-colors transition-colors border-b border-outline/5 last:border-b-0">
                    <td class="p-4 font-black tracking-widest text-[10px] text-primary">#ORD-${order.id}</td>
                    <td class="p-4">
                        <p class="text-xs font-bold text-on-surface">${order.user_id}</p>
                    </td>
                    <td class="p-4">
                        <span class="text-xs font-bold">S/ ${order.total_price.toFixed(2)}</span>
                    </td>
                    <td class="p-4">
                        <span class="px-2 py-0.5 ${statusColor} rounded text-[10px]">${order.status}</span>
                    </td>
                    <td class="p-4 text-right text-xs text-on-surface-variant font-medium">
                        ${new Date(order.created_at).toLocaleString('es-PE')}
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch(error) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-error text-xs font-bold">Failed to load history</td></tr>`;
    }
}

// ==========================
// INVENTORY MODULE LOGIC
// ==========================

async function loadInventory() {
    if(!document.getElementById('inv-raw-materials')) return; // No estamos en inventario.html
    const token = localStorage.getItem('jhire_jwt_token');
    
    try {
        const res = await fetch('/api/inventory/', {
             headers: { 'Authorization': `Bearer ${token}` }
        });
        if(!res.ok) throw new Error('Error al conectar con Inventario');
        
        const data = await res.json();
        
        // Update KPIs
        document.getElementById('inv-raw-materials').innerHTML = `${data.raw_materials.toLocaleString('en-US')} <span class="text-sm text-outline">unidades</span>`;
        document.getElementById('inv-finished-products').innerHTML = `${data.finished_products.toLocaleString('en-US')} <span class="text-sm text-outline">unidades</span>`;
        document.getElementById('inv-low-stock').innerHTML = `${data.low_stock_items.toLocaleString('en-US')} <span class="text-sm ${data.low_stock_items > 0 ? 'text-error' : 'text-outline'}">SKUs</span>`;
        document.getElementById('inv-movements-count').innerHTML = `${data.total_movements_week.toLocaleString('en-US')} <span class="text-sm text-outline">registros</span>`;
        
        // Update AI
        const aiBox = document.getElementById('inv-ai-suggestion');
        if(aiBox) {
            aiBox.innerHTML = `<span class="w-2 h-2 rounded-full ${data.low_stock_items > 0 ? 'bg-error' : 'bg-success'} animate-pulse"></span> ${data.ai_suggestion}`;
            if(data.low_stock_items > 0) aiBox.classList.replace('text-outline', 'text-error');
            else aiBox.classList.replace('text-error', 'text-outline');
        }
        
        // Render Suppliers
        const supplierBox = document.getElementById('supplierContainer');
        if(supplierBox && data.suppliers) {
            supplierBox.innerHTML = data.suppliers.map(s => `
                <div class="bg-surface p-4 border border-outline-variant/30 rounded-xl hover:border-primary/50 transition-colors">
                    <p class="font-bold text-sm text-primary">${s.name}</p>
                    <p class="text-xs text-outline mt-1"><span class="material-symbols-outlined text-[12px]">local_shipping</span> Lead Time: <span class="font-bold cursor-text">${s.lead_time}</span></p>
                </div>
            `).join('') || '<p class="text-xs text-outline text-center p-4">No hay proveedores en la BBDD</p>';
        }
        
        // Render Movements Log
        const movTable = document.getElementById('movementTableBody');
        if(movTable && data.movements) {
            movTable.innerHTML = data.movements.map(m => {
                const isEntrada = m.desc.includes('[Entrada]');
                return `
                <tr class="hover:bg-surface-container-high transition-colors transition-colors">
                    <td class="p-3 font-bold text-xs text-on-surface">${m.sku}</td>
                    <td class="p-3 text-xs text-outline">${m.desc}</td>
                    <td class="p-3 text-right">
                        <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${isEntrada ? 'bg-success/10 text-success' : 'bg-error-container text-on-error-container'}">
                            ${isEntrada ? 'ENTRADA' : 'SALIDA'}
                        </span>
                    </td>
                </tr>
            `}).join('') || '<tr><td colspan="3" class="p-4 text-center text-xs text-outline">No hay movimientos recientes.</td></tr>';
        }
        
    } catch(e) {
        console.error(e);
        Swal.fire({ icon: 'error', title: 'Falla Técnica', text: e.message, background: 'var(--color-surface)', color: 'var(--color-on-surface)' });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    
    // Registrar EventListener form
    const movForm = document.getElementById('movementForm');
    if(movForm) {
        movForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const token = localStorage.getItem('jhire_jwt_token');
            const payload = {
                product_id: parseInt(document.getElementById('movProductId').value),
                type: document.getElementById('movType').value,
                quantity: parseInt(document.getElementById('movQuantity').value),
                date: new Date().toISOString()
            };
            
            try {
                const res = await fetch('/api/inventory/movement', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify(payload)
                });
                
                if(!res.ok) {
                    const errorJson = await res.json();
                    throw new Error(errorJson.detail || 'Fallo al procesar operación');
                }
                
                Swal.fire({
                    icon: 'success',
                    title: '¡Aprobado!',
                    text: 'El inventario y almacén se han movido lógicamente.',
                    background: 'var(--color-surface)',
                    color: 'var(--color-on-surface)',
                    confirmButtonColor: 'var(--color-primary)'
                });
                
                document.getElementById('movementModal').classList.add('hidden');
                movForm.reset();
                loadInventory();
                
            } catch(error) {
                Swal.fire({
                    icon: 'error',
                    title: 'Transacción Bloqueada',
                    text: error.message,
                    background: 'var(--color-surface)',
                    color: 'var(--color-on-surface)'
                });
            }
        });
    }
    
            // --- LÓGICA CRM DINÁMICA ---
    const loadDynamicCRM = async () => {
        const token = localStorage.getItem('jhire_jwt_token');
        let clientsData = [];
        
        const crmClientsTableBody = document.getElementById('crmClientsTableBody');
        if (crmClientsTableBody) {
            try {
                const res = await fetch('/api/crm/clients', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const clients = await res.json();
                    clientsData = clients;
                    if(clients.length > 0) {
                        crmClientsTableBody.innerHTML = clients.map(client => `
                            <tr class="hover:bg-surface-container-high transition-colors bg-surface dark:bg-surface-container cursor-pointer" onclick="analyzeCRMProfile(${client.id}, '${client.name}')">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(client.name)}&background=random" class="w-8 h-8 rounded-full border border-outline-variant/30">
                                        <div>
                                            <p class="text-xs font-bold text-on-surface">${client.name}</p>
                                            <p class="text-[10px] text-on-surface-variant">ID: #${client.id}</p>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <p class="text-xs font-medium text-slate-500 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">mail</span> ${client.email}</p>
                                    <p class="text-[10px] text-slate-500 mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">call</span> ${client.phone || 'No registrado'}</p>
                                </td>
                                <td class="px-6 py-4">
                                    <p class="text-xs font-bold">${client.company}</p>
                                    <p class="text-[10px] text-on-surface-variant">RUC/DNI: ${client.ruc_dni}</p>
                                </td>
                                <td class="px-6 py-4 text-center">
                                    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-tertiary-container/30 text-tertiary-container font-bold text-[10px]">
                                        ${client.interactions_count}
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-right">
                                    <div class="flex justify-end gap-2">
                                        <button onclick="event.stopPropagation(); window.open('mailto:${client.email}')" class="py-1 px-2.5 bg-surface-container hover:bg-primary/10 hover:text-primary rounded text-on-surface text-[10px] font-bold flex items-center gap-1 transition-colors border border-outline-variant/30">
                                            <span class="material-symbols-outlined text-[14px]">mail</span> Mensaje
                                        </button>
                                        <button onclick="event.stopPropagation(); window.open('https://wa.me/${client.phone ? client.phone.replace(/\D/g,'') : ''}')" class="py-1 px-2.5 bg-surface-container hover:bg-green-100 hover:text-green-700 rounded text-on-surface text-[10px] font-bold flex items-center gap-1 transition-colors border border-outline-variant/30">
                                            <span class="material-symbols-outlined text-[14px]">chat</span> WhatsApp
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('');
                    } else {
                        crmClientsTableBody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-xs text-outline-variant">Aún no hay clientes registrados en la BD.</td></tr>';
                    }
                }
            } catch(e) {
                console.error('Error fetching CRM clients:', e);
            }
        }
        
        // Re-use clients endpoint to dynamically calculate REAL CRM KPIs
        const crmFunnelContainer = document.getElementById('crmFunnelContainer');
        if (crmFunnelContainer && clientsData) {
            try {
                // Generate funnel data based on clients real interactions
                const totalClients = clientsData.length;
                const contactados = clientsData.filter(c => c.interactions_count >= 1).length;
                const enProceso = clientsData.filter(c => c.interactions_count >= 3).length;
                const fidelizados = clientsData.filter(c => c.interactions_count >= 6).length;
                
                crmFunnelContainer.innerHTML = `
                    <div class="funnel-step flex-1 bg-primary flex flex-col items-center justify-center text-on-primary relative">
                        <span class="text-2xl font-black">${totalClients}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Registrados</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/85 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${contactados}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Contactados</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/70 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${enProceso}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Activos</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/55 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${fidelizados}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Fidelizados</span>
                    </div>
                `;
                
                const kpiValorTotal = document.getElementById('kpiValorTotal');
                const kpiCicloProm = document.getElementById('kpiCicloProm');
                const kpiConversion = document.getElementById('kpiConversion');
                
                if (kpiValorTotal) {
                    const totalInteracciones = clientsData.reduce((sum, c) => sum + c.interactions_count, 0);
                    kpiValorTotal.innerText = totalInteracciones.toString() + ' Puntos';
                }
                if(kpiCicloProm) {
                    const promResult = totalClients > 0 ? (clientsData.reduce((sum, c) => sum + c.interactions_count, 0) / totalClients).toFixed(1) : 0;
                    kpiCicloProm.innerText = promResult;
                }
                if(kpiConversion) {
                    const retentionRate = totalClients > 0 ? (contactados / totalClients) * 100 : 0;
                    kpiConversion.innerText = retentionRate.toFixed(1) + '%';
                }
                
                // Small KPI Card - Frequent Clients
                const kpiFrequentCount = document.getElementById('kpiFrequentCount');
                const kpiFrequentBar = document.getElementById('kpiFrequentBar');
                if(kpiFrequentCount && kpiFrequentBar) {
                    const freqRate = totalClients > 0 ? (fidelizados / totalClients) * 100 : 0;
                    kpiFrequentCount.innerText = freqRate.toFixed(1) + '%';
                    kpiFrequentBar.style.width = freqRate + '%';
                }
                
            } catch(e) {
                console.error("Funnel processing error:", e);
            }
        }
    };

    // Globally exposed function to trigger AI analysis
    window.analyzeCRMProfile = async (userId, userName) => {
        const emptyState = document.getElementById('crmAiEmptyState');
        const loadingState = document.getElementById('crmAiLoading');
        const resultsState = document.getElementById('crmAiResults');
        const clientNameEl = document.getElementById('aiClientName');
        const clientStatusEl = document.getElementById('aiClientStatus');
        const listEl = document.getElementById('aiRecommendationsList');
        
        if(!emptyState || !loadingState || !resultsState) return;
        
        // Ensure styling transition is smooth
        emptyState.classList.add('hidden');
        resultsState.classList.add('hidden');
        loadingState.classList.remove('hidden');
        
        try {
            const token = localStorage.getItem('jhire_jwt_token');
            const res = await fetch(`/api/crm/recommendations/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            // Artificial delay to show processing "AI"
            setTimeout(() => {
                loadingState.classList.add('hidden');
                
                clientNameEl.innerText = userName;
                clientStatusEl.innerText = data.message || 'Activo';
                
                // Color formatting based on behavioral segment
                const segmentColors = {
                    'Cliente VIP': 'bg-green-100 text-green-700',
                    'En Riesgo': 'bg-red-100 text-red-700',
                    'Cliente Frecuente': 'bg-blue-100 text-blue-700',
                    'Cliente Ocasional': 'bg-amber-100 text-amber-700',
                    'Nuevo Prospecto': 'bg-gray-100 text-gray-600'
                };
                const colorClass = segmentColors[data.message] || 'bg-primary/10 text-primary';
                clientStatusEl.className = `inline-flex mt-2 items-center px-2 py-0.5 rounded text-[10px] font-bold ${colorClass} uppercase`;
                
                listEl.innerHTML = '';
                
                // Show behavioral metrics if available
                if(data.metrics && data.metrics.total_orders > 0) {
                    listEl.innerHTML += `
                    <li class="p-3 bg-surface-container-low rounded-lg text-[11px] text-on-surface grid grid-cols-3 gap-2 text-center border border-outline-variant/20">
                        <div>
                            <p class="text-[9px] text-outline uppercase font-bold">Pedidos</p>
                            <p class="text-lg font-black text-primary">${data.metrics.total_orders}</p>
                        </div>
                        <div>
                            <p class="text-[9px] text-outline uppercase font-bold">Ticket Prom.</p>
                            <p class="text-lg font-black text-primary">S/ ${data.metrics.avg_ticket.toFixed(0)}</p>
                        </div>
                        <div>
                            <p class="text-[9px] text-outline uppercase font-bold">Últ. Compra</p>
                            <p class="text-lg font-black text-primary">${data.metrics.days_since_last}d</p>
                        </div>
                    </li>`;
                }
                
                if(data.recommendations && data.recommendations.length > 0) {
                    data.recommendations.forEach(rec => {
                        listEl.innerHTML += `
                        <li class="p-3 bg-surface border border-outline-variant/10 rounded-lg shadow-sm flex gap-3 text-[11px] text-on-surface-variant leading-relaxed">
                            <span>${rec}</span>
                        </li>`;
                    });
                } else {
                    listEl.innerHTML += `<p class="text-xs text-outline">No hay recomendaciones algorítmicas en este momento.</p>`;
                }
                
                resultsState.classList.remove('hidden');
            }, 800);
            
        } catch(e) {
            loadingState.classList.add('hidden');
            emptyState.classList.remove('hidden');
            console.error(e);
        }
    };

    // =====================================================
    // CRM: MODAL & ACTION LOGIC
    // =====================================================

    // State: currently selected CRM client
    window._crmSelectedClient = null;

    // Override analyzeCRMProfile to also store the selected client
    const _originalAnalyze = window.analyzeCRMProfile;
    window.analyzeCRMProfile = async (userId, userName) => {
        window._crmSelectedClient = { id: userId, name: userName };
        await _originalAnalyze(userId, userName);
        // Load interaction history
        loadInteractionHistory(userId);
    };

    // --- MODAL HELPERS ---
    const openModal = (id) => {
        const m = document.getElementById(id);
        if (!m) return;
        m.classList.remove('pointer-events-none');
        setTimeout(() => m.classList.remove('opacity-0'), 10);
    };
    const closeModal = (id) => {
        const m = document.getElementById(id);
        if (!m) return;
        m.classList.add('opacity-0');
        setTimeout(() => m.classList.add('pointer-events-none'), 300);
    };

    // --- EMAIL MODAL ---
    window.openEmailModal = () => {
        if (!window._crmSelectedClient) {
            Swal.fire('Selecciona un Cliente', 'Haz click en un cliente de la tabla para activar las acciones CRM.', 'info');
            return;
        }
        document.getElementById('emailUserId').value = window._crmSelectedClient.id;
        document.getElementById('emailModalClientLabel').innerText = `Cliente: ${window._crmSelectedClient.name}`;
        document.getElementById('emailSubject').value = '';
        document.getElementById('emailCustomMsg').value = '';
        openModal('emailModal');
    };
    window.closeEmailModal = () => closeModal('emailModal');

    const crmEmailForm = document.getElementById('crmEmailForm');
    if (crmEmailForm) {
        crmEmailForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userId = document.getElementById('emailUserId').value;
            const template = document.getElementById('emailTemplate').value;
            const subject = document.getElementById('emailSubject').value.trim();
            const customMsg = document.getElementById('emailCustomMsg').value.trim();

            Swal.fire({ title: 'Enviando Email...', html: 'Procesando comunicación CRM vía SMTP...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

            try {
                const token = localStorage.getItem('jhire_jwt_token');
                const res = await fetch('/api/crm/send-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        template: template,
                        subject: subject || null,
                        custom_message: customMsg || null
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    closeEmailModal();
                    Swal.fire({
                        icon: 'success',
                        title: '¡Email Enviado!',
                        html: `<div class="text-left text-sm mt-2">
                            <p><strong>Destinatario:</strong> ${data.recipient}</p>
                            <p><strong>Plantilla:</strong> ${data.template_used}</p>
                            <p class="text-green-600 font-bold mt-2">✓ Interacción registrada automáticamente en el CRM</p>
                        </div>`,
                    });
                    loadInteractionHistory(parseInt(userId));
                } else {
                    Swal.fire('Error', data.detail || 'No se pudo enviar el email', 'error');
                }
            } catch (err) {
                Swal.fire('Error de Conexión', err.message, 'error');
            }
        });
    }

    // --- WHATSAPP MODAL ---
    window.openWhatsAppModal = () => {
        if (!window._crmSelectedClient) {
            Swal.fire('Selecciona un Cliente', 'Haz click en un cliente de la tabla para activar las acciones CRM.', 'info');
            return;
        }
        document.getElementById('waUserId').value = window._crmSelectedClient.id;
        document.getElementById('waModalClientLabel').innerText = `Cliente: ${window._crmSelectedClient.name}`;
        document.getElementById('waMessageType').value = 'cotizacion';
        document.getElementById('waCustomMsgContainer').classList.add('hidden');
        updateWAPreview();
        openModal('whatsAppModal');
    };
    window.closeWhatsAppModal = () => closeModal('whatsAppModal');

    window.updateWAPreview = () => {
        const type = document.getElementById('waMessageType').value;
        const name = window._crmSelectedClient?.name || 'Cliente';
        const container = document.getElementById('waCustomMsgContainer');

        if (type === 'personalizado') {
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
        }

        const previews = {
            cotizacion: `Hola ${name}, le saluda el equipo comercial de *JHIRE*. 🏭\n\nLe recordamos que tiene una cotización pendiente de revisión...\n\n_Equipo Comercial JHIRE_`,
            seguimiento: `Hola ${name}, le saluda *JHIRE*. 🤝\n\nQueremos asegurarnos de que su último pedido haya llegado en perfectas condiciones...\n\n_Equipo de Atención al Cliente JHIRE_`,
            recordatorio_pago: `Hola ${name}, le saluda el área de cobranzas de *JHIRE*. 📋\n\nLe recordamos amablemente que tiene una cuota de pago pendiente...\n\n_Área de Cobranzas JHIRE_`,
            personalizado: `Hola ${name}, le saluda *JHIRE*.\n\n(Escribe tu mensaje arriba)`
        };
        document.getElementById('waPreviewText').innerText = previews[type] || previews.personalizado;
    };

    const crmWhatsAppForm = document.getElementById('crmWhatsAppForm');
    if (crmWhatsAppForm) {
        crmWhatsAppForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userId = document.getElementById('waUserId').value;
            const messageType = document.getElementById('waMessageType').value;
            const customMsg = document.getElementById('waCustomMsg')?.value?.trim() || null;

            try {
                const token = localStorage.getItem('jhire_jwt_token');
                const res = await fetch('/api/crm/whatsapp-link', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        message_type: messageType,
                        custom_message: customMsg
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    closeWhatsAppModal();
                    window.open(data.whatsapp_link, '_blank');
                    Swal.fire({
                        icon: 'success',
                        title: 'WhatsApp Abierto',
                        html: `<p class="text-sm">Se abrió WhatsApp con el mensaje pre-armado para el cliente.</p>
                        <p class="text-green-600 font-bold text-xs mt-2">✓ Interacción registrada en CRM</p>`,
                        timer: 3000,
                        showConfirmButton: false
                    });
                    loadInteractionHistory(parseInt(userId));
                } else {
                    Swal.fire('Error', data.detail || 'No se pudo generar el link de WhatsApp', 'error');
                }
            } catch (err) {
                Swal.fire('Error de Conexión', err.message, 'error');
            }
        });
    }

    // --- INTERACTION MODAL ---
    window.openInteractionModal = () => {
        if (!window._crmSelectedClient) {
            Swal.fire('Selecciona un Cliente', 'Haz click en un cliente de la tabla para activar las acciones CRM.', 'info');
            return;
        }
        document.getElementById('intUserId').value = window._crmSelectedClient.id;
        document.getElementById('intModalClientLabel').innerText = `Cliente: ${window._crmSelectedClient.name}`;
        document.getElementById('intNotes').value = '';
        openModal('interactionModal');
    };
    window.closeInteractionModal = () => closeModal('interactionModal');

    const crmInteractionForm = document.getElementById('crmInteractionForm');
    if (crmInteractionForm) {
        crmInteractionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userId = document.getElementById('intUserId').value;
            const intType = document.querySelector('input[name="intType"]:checked')?.value || 'nota';
            const notes = document.getElementById('intNotes').value.trim();

            if (!notes) {
                Swal.fire('Campo Requerido', 'Las notas de la interacción no pueden estar vacías.', 'warning');
                return;
            }

            try {
                const token = localStorage.getItem('jhire_jwt_token');
                const res = await fetch('/api/crm/interactions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        user_id: parseInt(userId),
                        type: intType,
                        notes: notes
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    closeInteractionModal();
                    Swal.fire({
                        icon: 'success',
                        title: 'Interacción Registrada',
                        text: data.message,
                        timer: 2500,
                        showConfirmButton: false
                    });
                    loadInteractionHistory(parseInt(userId));
                } else {
                    Swal.fire('Error', data.detail || 'No se pudo registrar la interacción', 'error');
                }
            } catch (err) {
                Swal.fire('Error de Conexión', err.message, 'error');
            }
        });
    }

    // --- DISPATCH ACTION (Connected to AI panel) ---
    window.dispatchCRMAction = async () => {
        if (!window._crmSelectedClient) {
            Swal.fire('Selecciona un Cliente', 'Haz click en un cliente de la tabla para que la IA analice y recomiende acciones.', 'info');
            return;
        }
        // Determine best template based on AI segment
        const statusEl = document.getElementById('aiClientStatus');
        const segment = statusEl?.innerText?.trim() || '';
        
        let template = 'seguimiento';
        if (segment.includes('Nuevo')) template = 'bienvenida';
        else if (segment.includes('Riesgo')) template = 'reactivacion';
        else if (segment.includes('VIP')) template = 'seguimiento';
        else if (segment.includes('Ocasional')) template = 'cotizacion';

        const { isConfirmed } = await Swal.fire({
            title: 'Despachar Acción IA',
            html: `<div class="text-left text-sm">
                <p>Se enviará un email automático al cliente <strong>${window._crmSelectedClient.name}</strong> basado en su segmento:</p>
                <p class="mt-2 font-bold text-primary">Segmento: ${segment}</p>
                <p class="mt-1">Plantilla: <strong>${template.toUpperCase()}</strong></p>
            </div>`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Enviar Email',
            cancelButtonText: 'Cancelar'
        });

        if (!isConfirmed) return;

        Swal.fire({ title: 'Despachando...', html: 'Enviando comunicación CRM automatizada...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        try {
            const token = localStorage.getItem('jhire_jwt_token');
            const res = await fetch('/api/crm/send-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({
                    user_id: window._crmSelectedClient.id,
                    template: template
                })
            });
            const data = await res.json();
            if (res.ok) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Acción Despachada!',
                    html: `<div class="text-left text-sm mt-2">
                        <p>✓ Email <strong>${data.template_used}</strong> enviado a <strong>${data.recipient}</strong></p>
                        <p class="text-green-600 font-bold mt-2">Interacción #${data.interaction_id} registrada en CRM</p>
                    </div>`
                });
                loadInteractionHistory(window._crmSelectedClient.id);
            } else {
                Swal.fire('Error', data.detail || 'Error despachando acción', 'error');
            }
        } catch (err) {
            Swal.fire('Error de Conexión', err.message, 'error');
        }
    };

    // --- INTERACTION HISTORY ---
    window.loadInteractionHistory = async (userId) => {
        const historyList = document.getElementById('interactionHistoryList');
        if (!historyList) return;

        try {
            const token = localStorage.getItem('jhire_jwt_token');
            const res = await fetch(`/api/crm/clients/${userId}/interactions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const interactions = await res.json();
                if (interactions.length === 0) {
                    historyList.innerHTML = '<p class="text-[10px] text-outline text-center py-2">Sin interacciones registradas.</p>';
                } else {
                    const typeIcons = { email: 'mail', whatsapp: 'chat', llamada: 'call', visita: 'location_on', nota: 'sticky_note_2' };
                    const typeColors = { email: 'text-primary', whatsapp: 'text-green-600', llamada: 'text-blue-600', visita: 'text-amber-600', nota: 'text-purple-600' };
                    historyList.innerHTML = interactions.slice(0, 10).map(i => {
                        const d = new Date(i.date);
                        const dateStr = `${d.getDate().toString().padStart(2,'0')}/${(d.getMonth()+1).toString().padStart(2,'0')} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
                        return `<div class="flex gap-2 p-2 bg-surface-container-low rounded-lg border border-outline-variant/10">
                            <span class="material-symbols-outlined text-[14px] ${typeColors[i.type] || 'text-outline'} shrink-0 mt-0.5">${typeIcons[i.type] || 'info'}</span>
                            <div class="min-w-0">
                                <p class="text-[10px] text-on-surface font-medium truncate">${i.notes}</p>
                                <p class="text-[9px] text-outline">${dateStr}</p>
                            </div>
                        </div>`;
                    }).join('');
                }
                // Show the list
                historyList.classList.remove('hidden');
                const icon = document.getElementById('historyToggleIcon');
                if (icon) icon.innerText = 'expand_less';
            }
        } catch (e) {
            console.error('Error loading interactions:', e);
        }
    };

    window.toggleInteractionHistory = () => {
        const list = document.getElementById('interactionHistoryList');
        const icon = document.getElementById('historyToggleIcon');
        if (!list) return;
        if (list.classList.contains('hidden')) {
            list.classList.remove('hidden');
            if (icon) icon.innerText = 'expand_less';
        } else {
            list.classList.add('hidden');
            if (icon) icon.innerText = 'expand_more';
        }
    };

    // --- LÓGICA FACTURACIÓN DINÁMICA ---
    const loadDynamicBilling = async () => {
        const invContainer = document.getElementById('recentInvoicesContainer');
        if(invContainer) {
            const token = localStorage.getItem('jhire_jwt_token');
            try {
                const res = await fetch('/api/billing/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if(res.ok) {
                    const invoices = await res.json();
                    if(invoices.length > 0) {
                        invContainer.innerHTML = invoices.slice(0, 5).map(i => `
                        <div class="flex items-center justify-between p-3 border-b border-outline-variant/10 bg-surface dark:bg-surface-container hover:bg-surface-container-low transition-colors group cursor-pointer invoice-detail-btn" data-inv-id="${i.id}" data-inv-number="${i.invoice_number}" data-inv-ruc="${i.client_ruc_dni}" data-inv-name="${(i.client_name || '').replace(/"/g, '&quot;')}" data-inv-subtotal="${i.subtotal}" data-inv-igv="${i.igv}" data-inv-total="${i.total}">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded ${i.sunat_status === 'Emitida' ? 'bg-green-100 text-green-700' : 'bg-surface-container/20 text-on-surface-variant'} flex items-center justify-center shadow-sm">
                                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">${i.sunat_status === 'Emitida' ? 'check_circle' : 'hourglass_empty'}</span>
                                </div>
                                <div>
                                    <p class="text-sm font-black text-primary group-hover:underline">${i.invoice_number}</p>
                                    <p class="text-[10px] text-on-surface-variant font-bold mt-[2px]">${i.client_name} <span class="bg-surface-container-high px-1 rounded ml-1 text-outline">RUC: ${i.client_ruc_dni}</span></p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-black text-on-surface">S/ ${parseFloat(i.total).toFixed(2)}</p>
                                <span class="text-[9px] font-black ${i.sunat_status === 'Emitida' ? 'text-green-600 bg-green-50 px-1 py-0.5 rounded' : 'text-on-surface-variant'} uppercase flex items-center justify-end gap-1"><span class="material-symbols-outlined text-[10px]">cloud_done</span> ${i.sunat_status} SUNAT</span>
                            </div>
                        </div>
                        `).join('');
                        
                        // Attach click handlers safely (no inline JS)
                        invContainer.querySelectorAll('.invoice-detail-btn').forEach(el => {
                            el.addEventListener('click', () => {
                                const d = el.dataset;
                                Swal.fire({
                                    title: 'Detalle Comprobante Fiscal',
                                    html: `<div style="text-align:left;font-size:14px;" class="bg-surface-container-low p-4 rounded-lg">
                                        <p><strong>${d.invNumber}</strong></p>
                                        <p><strong>RUC:</strong> ${d.invRuc}</p>
                                        <p><strong>Razón:</strong> ${d.invName}</p>
                                        <hr style="margin:10px 0;border-color:#ccc">
                                        <div style="display:flex;justify-content:space-between"><p>Subtotal:</p><p>S/ ${parseFloat(d.invSubtotal).toFixed(2)}</p></div>
                                        <div style="display:flex;justify-content:space-between"><p>IGV(18%):</p><p>S/ ${parseFloat(d.invIgv).toFixed(2)}</p></div>
                                        <div style="display:flex;justify-content:space-between;font-weight:bold;margin-top:5px;"><p>Total:</p><p>S/ ${parseFloat(d.invTotal).toFixed(2)}</p></div>
                                    </div>`,
                                    icon: 'info',
                                    showCancelButton: true,
                                    confirmButtonText: 'Ver representación (PDF)',
                                    cancelButtonText: 'Cerrar'
                                }).then((result) => {
                                    if(result.isConfirmed) {
                                        window.open('/api/billing/' + d.invId + '/pdf', '_blank');
                                    }
                                });
                            });
                        });
                    } else {
                        invContainer.innerHTML = '<div class="p-8 text-center text-xs text-outline-variant flex flex-col items-center bg-surface-container-lowest rounded-lg border border-dashed border-outline/30"><span class="material-symbols-outlined text-4xl opacity-50 mb-2">receipt_long</span><p class="font-bold">Ningún comprobante fiscal emitido.</p></div>';
                    }
                }
            } catch(e) {}
        }
    };
    
    // Conflicting invoiceForm listener removed, handled in facturacion.html
    loadDynamicCRM();
    loadDynamicBilling();

    // ==========================================
    // INVENTORY MODULE
    // ==========================================
    if (document.getElementById('inv-raw-materials')) {
        let _invProducts = [];
        let _invLowStock = [];

        async function loadInventory() {
            try {
                const res = await fetch('/api/inventory/', { headers: authHeaders() });
                if (!res.ok) return;
                const d = await res.json();
                _invProducts = d.products || [];
                _invLowStock = d.low_stock_products || [];

                document.getElementById('inv-raw-materials').innerHTML = `${d.raw_materials} <span class="text-sm font-medium text-outline">unidades</span>`;
                document.getElementById('inv-finished-products').innerHTML = `${d.finished_products} <span class="text-sm font-medium text-outline">unidades</span>`;
                document.getElementById('inv-low-stock').innerHTML = `${d.low_stock_items} <span class="text-sm font-medium text-outline">SKUs</span>`;
                document.getElementById('inv-movements-count').innerHTML = `${d.total_movements_week} <span class="text-sm font-medium text-outline">registros</span>`;

                const sugEl = document.getElementById('inv-ai-suggestion');
                if (sugEl) sugEl.innerHTML = `<span class="w-2 h-2 rounded-full ${d.low_stock_items > 0 ? 'bg-error' : 'bg-success'} animate-pulse"></span> ${d.ai_suggestion}`;

                // Suppliers
                const sc = document.getElementById('supplierContainer');
                if (sc) {
                    if (d.suppliers.length === 0) {
                        sc.innerHTML = '<p class="text-outline text-sm text-center py-8">Sin proveedores registrados</p>';
                    } else {
                        sc.innerHTML = d.suppliers.map(s => `<div class="flex items-center justify-between p-3 bg-surface-container rounded-xl"><span class="font-bold text-sm text-on-surface">${s.name}</span><span class="text-xs text-outline font-medium bg-surface px-2 py-1 rounded-lg">${s.lead_time}</span></div>`).join('');
                    }
                }

                // Movements table
                const tb = document.getElementById('movementTableBody');
                if (tb) {
                    if (d.movements.length === 0) {
                        tb.innerHTML = '<tr><td colspan="3" class="text-center py-8 text-outline text-sm">Sin movimientos registrados</td></tr>';
                    } else {
                        tb.innerHTML = d.movements.map(m => `<tr class="hover:bg-surface-container/50 transition-colors"><td class="p-3 font-bold text-primary text-xs">${m.sku}</td><td class="p-3 text-on-surface">${m.desc}</td><td class="p-3 text-right"><span class="px-2 py-1 rounded-lg text-xs font-bold ${m.type === 'Entrada' ? 'bg-success-container text-success' : 'bg-red-100 text-error'}">${m.type}</span></td></tr>`).join('');
                    }
                }
            } catch (e) { console.error('Inventory load error', e); }
        }

        // Make KPI cards clickable
        document.querySelectorAll('[data-inv-detail]').forEach(card => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                const type = card.dataset.invDetail;
                let title = '', items = [];
                if (type === 'raw') { title = 'Insumos / Componentes'; items = _invProducts; }
                else if (type === 'finished') { title = 'Productos para Venta'; items = _invProducts; }
                else if (type === 'low') { title = 'Escasez Crítica (Stock < 20)'; items = _invLowStock; }
                else if (type === 'movements') { title = 'Movimientos del Mes'; showMovementsModal(); return; }
                showProductDrillModal(title, items, type);
            });
        });

        function showProductDrillModal(title, items, type) {
            let existing = document.getElementById('invDrillModal');
            if (existing) existing.remove();
            const modal = document.createElement('div');
            modal.id = 'invDrillModal';
            modal.className = 'fixed inset-0 bg-on-surface/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4';
            const rows = items.length === 0
                ? '<tr><td colspan="5" class="text-center py-8 text-outline">No hay productos en esta categoría</td></tr>'
                : items.map(p => {
                    const stockClass = p.stock < 20 ? 'text-error font-black' : 'text-on-surface';
                    return `<tr class="hover:bg-surface-container/50 transition-colors border-b border-outline-variant/10">
                        <td class="p-3 text-xs font-bold text-primary">JHIRE-${p.id}</td>
                        <td class="p-3 font-medium text-sm">${p.name}</td>
                        <td class="p-3"><span class="px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase bg-surface-container-high text-on-surface">${p.category}</span></td>
                        <td class="p-3 ${stockClass} text-right font-bold">${p.stock}</td>
                        <td class="p-3 text-right text-sm font-medium">S/. ${p.price_soles.toFixed(2)}</td>
                    </tr>`;
                }).join('');
            modal.innerHTML = `<div class="bg-surface rounded-2xl w-full max-w-3xl max-h-[80vh] overflow-hidden shadow-2xl border border-outline-variant/20 flex flex-col">
                <div class="p-5 border-b border-outline-variant/20 bg-surface-container-low flex justify-between items-center">
                    <div><h3 class="text-lg font-bold font-headline">${title}</h3><p class="text-xs text-outline mt-0.5">${items.length} productos encontrados</p></div>
                    <button onclick="document.getElementById('invDrillModal').remove()" class="text-outline hover:text-error transition-colors"><span class="material-symbols-outlined">close</span></button>
                </div>
                <div class="overflow-y-auto flex-1"><table class="w-full text-left"><thead class="bg-surface-container sticky top-0"><tr class="text-[10px] font-black uppercase text-outline tracking-wider">
                    <th class="p-3">SKU</th><th class="p-3">Producto</th><th class="p-3">Categoría</th><th class="p-3 text-right">Stock</th><th class="p-3 text-right">Precio</th>
                </tr></thead><tbody>${rows}</tbody></table></div>
            </div>`;
            document.body.appendChild(modal);
            modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
        }

        function showMovementsModal() {
            const tb = document.getElementById('movementTableBody');
            if (!tb) return;
            let existing = document.getElementById('invDrillModal');
            if (existing) existing.remove();
            const modal = document.createElement('div');
            modal.id = 'invDrillModal';
            modal.className = 'fixed inset-0 bg-on-surface/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4';
            modal.innerHTML = `<div class="bg-surface rounded-2xl w-full max-w-3xl max-h-[80vh] overflow-hidden shadow-2xl border border-outline-variant/20 flex flex-col">
                <div class="p-5 border-b border-outline-variant/20 bg-surface-container-low flex justify-between items-center">
                    <h3 class="text-lg font-bold font-headline">Historial de Movimientos</h3>
                    <button onclick="document.getElementById('invDrillModal').remove()" class="text-outline hover:text-error transition-colors"><span class="material-symbols-outlined">close</span></button>
                </div>
                <div class="overflow-y-auto flex-1 p-5"><table class="w-full text-left"><thead class="bg-surface-container"><tr class="text-[10px] font-black uppercase text-outline tracking-wider"><th class="p-3">SKU</th><th class="p-3">Detalle</th><th class="p-3 text-right">Estado</th></tr></thead><tbody>${tb.innerHTML}</tbody></table></div>
            </div>`;
            document.body.appendChild(modal);
            modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
        }

        // Movement form
        const mf = document.getElementById('movementForm');
        if (mf) {
            mf.addEventListener('submit', async (e) => {
                e.preventDefault();
                const payload = { product_id: parseInt(document.getElementById('movProductId').value), type: document.getElementById('movType').value, quantity: parseInt(document.getElementById('movQuantity').value) };
                try {
                    const res = await fetch('/api/inventory/movement', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(payload) });
                    const data = await res.json();
                    if (res.ok) { Swal.fire({ icon: 'success', title: 'Registrado', text: data.message, timer: 1500, showConfirmButton: false }); document.getElementById('movementModal').classList.add('hidden'); mf.reset(); loadInventory(); }
                    else { Swal.fire({ icon: 'error', title: 'Error', text: data.detail }); }
                } catch (err) { Swal.fire({ icon: 'error', title: 'Error de Red', text: err.message }); }
            });
        }
        loadInventory();
    }

    // ==========================================
    // ADMIN CATALOG MODULE
    // ==========================================
    if (document.getElementById('catalogGrid')) {
        let _catProducts = [];
        async function loadCatalog() {
            try {
                const res = await fetch('/api/products', { headers: authHeaders() });
                if (!res.ok) return;
                _catProducts = await res.json();
                renderCatalog(_catProducts);
            } catch (e) { console.error('Catalog load error', e); }
        }

        function renderCatalog(products) {
            const grid = document.getElementById('catalogGrid');
            const countEl = document.getElementById('catalogCount');
            if (countEl) countEl.textContent = products.length;
            if (products.length === 0) {
                grid.innerHTML = '<div class="col-span-full text-center py-16"><span class="material-symbols-outlined text-6xl text-outline-variant/40 mb-4 block">inventory_2</span><p class="text-outline text-lg font-bold">Sin productos</p></div>';
                return;
            }
            grid.innerHTML = products.map(p => {
                const stockColor = p.stock < 20 ? 'text-error' : p.stock < 50 ? 'text-yellow-600' : 'text-success';
                const stockBg = p.stock < 20 ? 'bg-red-50' : p.stock < 50 ? 'bg-yellow-50' : 'bg-green-50';
                return `<div class="bg-surface-container-low rounded-2xl border border-outline-variant/20 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all group">
                    <div class="h-40 bg-surface-container flex items-center justify-center overflow-hidden">
                        <img src="${p.image_url || '/assets/images/escobilla_1.png'}" alt="${p.name}" class="h-full w-full object-cover group-hover:scale-105 transition-transform" onerror="this.src='/assets/images/escobilla_1.png'">
                    </div>
                    <div class="p-4 space-y-2">
                        <p class="text-[10px] font-black text-primary uppercase tracking-widest">SKU: JHIRE-${p.id}</p>
                        <h4 class="text-sm font-bold text-on-surface leading-tight line-clamp-2">${p.name}</h4>
                        <div class="flex items-center justify-between pt-2 border-t border-outline-variant/10">
                            <span class="text-lg font-black text-primary">S/. ${p.price_soles.toFixed(2)}</span>
                            <span class="${stockBg} ${stockColor} px-2 py-1 rounded-lg text-[10px] font-black">${p.stock} uds</span>
                        </div>
                        <div class="flex gap-2 pt-2">
                            <button onclick="editProduct(${p.id})" class="flex-1 px-3 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-1"><span class="material-symbols-outlined text-sm">edit</span>Editar</button>
                            <button onclick="deleteProduct(${p.id})" class="px-3 py-2 bg-error/10 text-error text-xs font-bold rounded-lg hover:bg-error/20 transition-colors"><span class="material-symbols-outlined text-sm">delete</span></button>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }

        // Search filter
        const catSearch = document.getElementById('catalogSearch');
        if (catSearch) {
            catSearch.addEventListener('input', () => {
                const q = catSearch.value.toLowerCase();
                renderCatalog(_catProducts.filter(p => p.name.toLowerCase().includes(q) || (p.id + '').includes(q)));
            });
        }

        // Category filter
        document.querySelectorAll('[data-cat-filter]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-cat-filter]').forEach(b => b.classList.remove('bg-primary', 'text-white'));
                btn.classList.add('bg-primary', 'text-white');
                const cat = btn.dataset.catFilter;
                renderCatalog(cat === 'all' ? _catProducts : _catProducts.filter(p => (p.category || 'general') === cat));
            });
        });

        // Add/Edit product modal
        window.showAddProductModal = function() {
            document.getElementById('productModalTitle').textContent = 'Agregar Producto';
            document.getElementById('productForm').reset();
            document.getElementById('productFormId').value = '';
            document.getElementById('productModal').classList.remove('hidden');
        };

        window.editProduct = function(id) {
            const p = _catProducts.find(x => x.id === id);
            if (!p) return;
            document.getElementById('productModalTitle').textContent = 'Editar Producto';
            document.getElementById('productFormId').value = p.id;
            document.getElementById('productFormName').value = p.name;
            document.getElementById('productFormPrice').value = p.price_soles;
            document.getElementById('productFormStock').value = p.stock;
            document.getElementById('productFormCategory').value = p.category || 'general';
            document.getElementById('productFormDesc').value = p.description || '';
            document.getElementById('productModal').classList.remove('hidden');
        };

        window.deleteProduct = function(id) {
            Swal.fire({ title: '¿Eliminar producto?', text: 'Esta acción no se puede deshacer', icon: 'warning', showCancelButton: true, confirmButtonColor: '#ba1a1a', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        const res = await fetch(`/api/products/${id}`, { method: 'DELETE', headers: authHeaders() });
                        if (res.ok || res.status === 404) { Swal.fire({ icon: 'success', title: 'Eliminado', timer: 1200, showConfirmButton: false }); loadCatalog(); }
                        else { const d = await res.json(); Swal.fire({ icon: 'error', title: 'Error', text: d.detail || 'Error al eliminar' }); }
                    } catch (e) { Swal.fire({ icon: 'error', title: 'Error', text: e.message }); }
                }
            });
        };

        const pf = document.getElementById('productForm');
        if (pf) {
            pf.addEventListener('submit', async (e) => {
                e.preventDefault();
                const id = document.getElementById('productFormId').value;
                const payload = {
                    name: document.getElementById('productFormName').value,
                    price_soles: parseFloat(document.getElementById('productFormPrice').value),
                    stock: parseInt(document.getElementById('productFormStock').value),
                    category: document.getElementById('productFormCategory').value,
                    description: document.getElementById('productFormDesc').value
                };
                try {
                    const url = id ? `/api/products/${id}` : '/api/products';
                    const method = id ? 'PUT' : 'POST';
                    const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(payload) });
                    if (res.ok) { Swal.fire({ icon: 'success', title: id ? 'Actualizado' : 'Creado', timer: 1200, showConfirmButton: false }); document.getElementById('productModal').classList.add('hidden'); loadCatalog(); }
                    else { const d = await res.json(); Swal.fire({ icon: 'error', title: 'Error', text: d.detail || 'Error' }); }
                } catch (e) { Swal.fire({ icon: 'error', title: 'Error', text: e.message }); }
            });
        }
        loadCatalog();
    }

    function authHeaders() {
        const t = localStorage.getItem('token');
        return t ? { 'Authorization': 'Bearer ' + t } : {};
    }
});
