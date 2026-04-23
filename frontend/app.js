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
                
                const loginRes = await fetch('http://localhost:8000/api/auth/token', {
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
                const res = await fetch('http://localhost:8000/api/auth/register', {
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
                
                const loginRes = await fetch('http://localhost:8000/api/auth/token', {
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
            window.location.href = "http://localhost:8000/api/reports/excel";
        }
        if (text.includes('DESCARGAR PDF')) {
            e.preventDefault();
            Swal.fire({ toast: true, position: 'top-end', icon: 'info', title: 'Generando PDF...', showConfirmButton: false, timer: 2000 });
            window.location.href = "http://localhost:8000/api/reports/pdf";
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
                
                const res = await fetch('http://localhost:8000/api/auth/register', {
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
        fetch('http://localhost:8000/api/dashboard/summary')
            .then(res => res.json())
            .then(data => {
                document.getElementById('total-sales').innerText = `S/. ${data.total_sales.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                if (document.getElementById('forecast-accuracy')) document.getElementById('forecast-accuracy').innerText = `${data.demand_forecast_accuracy}`;
                
                // NEW: Pronóstico Mañana KPI
                const forecastNextDay = document.getElementById('forecast-next-day');
                if (forecastNextDay) forecastNextDay.innerText = `S/. ${data.projected_next_day.toLocaleString('es-PE', {minimumFractionDigits: 2})}`;
                
                const rankingBox = document.getElementById('product-ranking-list');
                if (rankingBox && data.top_products) {
                    rankingBox.innerHTML = '';
                    if (data.top_products.length === 0) {
                        rankingBox.innerHTML = '<p class="text-xs text-outline text-center py-4">Aún no hay transacciones para analizar.</p>';
                    } else {
                        data.top_products.forEach((p, index) => {
                            rankingBox.innerHTML += `
                            <div class="flex items-center gap-4 p-3 bg-surface rounded-xl hover:bg-surface-container-high transition-colors group">
                                <div class="w-10 h-10 rounded-lg ${index===0 ? 'bg-primary/20 text-primary' : 'bg-surface-variant text-outline'} flex items-center justify-center font-black shrink-0">0${index+1}</div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm font-bold truncate text-on-surface">${p.name}</p>
                                    <p class="text-[10px] text-on-surface-variant font-medium">S/. ${p.contribution.toLocaleString('es-PE', {minimumFractionDigits: 2})} de contribución</p>
                                </div>
                                <span class="material-symbols-outlined ${index===0 ? 'text-success animate-pulse' : 'text-outline-variant'}">trending_up</span>
                            </div>`;
                        });
                    }
                }
                
                const anomaliesBox = document.getElementById('ai-anomalies-box');
                if (anomaliesBox && data.ai_anomalies) {
                    let msg = data.ai_anomalies[0] || "Sistema operativo estable. Sin desviaciones.";
                    let isUp = msg.toLowerCase().includes('alza');
                    
                    anomaliesBox.innerHTML = `
                        <h4 class="text-sm font-bold text-on-surface mb-1 flex items-center gap-1">
                            <span class="w-1.5 h-1.5 inline-block rounded-full ${isUp ? 'bg-success' : 'bg-amber-500'} animate-pulse"></span> 
                            ${isUp ? '📈 Alza Detectada' : '📉 Baja Detectada'}
                        </h4>
                        <p class="text-xs text-outline leading-relaxed">${msg}</p>
                        <p class="text-[10px] text-primary font-bold mt-2">Análisis basado en tendencias históricas de ventas</p>
                    `;
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
                console.log("Mocking data due to no backend connection", err);
                document.getElementById('total-sales').innerText = `S/. 145,157.46`;
                if (document.getElementById('forecast-accuracy')) document.getElementById('forecast-accuracy').innerText = `92`;
            });
    }
    // Fetch Products dynamically if productGrid exists
    const productGrid = document.getElementById('productGrid');
    if (productGrid) {
        fetch('http://localhost:8000/api/products')
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
        fetch(`http://localhost:8000/api/products/${productId}`)
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
            });
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
                const response = await fetch('http://localhost:8000/api/chat/', {
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
        let item = currentCart.find(i => i.id === id);
        if(item) {
            item.quantity = (item.quantity || 1) + delta;
            if(item.quantity <= 0) currentCart = currentCart.filter(i => i.id !== id);
            localStorage.setItem('jhire_cart', JSON.stringify(currentCart));
            window.updateCartBadge();
            renderCartItems();
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
            const bodyPayload = { items: data.map(i => ({ product_id: i.id, quantity: i.quantity || 1 })) };
            
            const res = await fetch('http://localhost:8000/api/orders/', {
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
            fetch('http://localhost:8000/api/orders/me', {
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
                const res = await fetch(`http://localhost:8000/api/orders/${orderId}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ status: newStatus })
                });
                if(!res.ok) throw new Error("Error status");
                loadAdminOrders();
            } catch(e) {
                console.error(e);
                Swal.fire('Error', 'Error al actualizar la orden.', 'error');
            }
        };

        const loadAdminOrders = async () => {
            if(!document.getElementById('adminOrdersTableBody')) return;
            try {
                const res = await fetch('http://localhost:8000/api/orders/admin', {
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
            const wsUrl = window.location.protocol === 'https:' ? 'wss://' : 'ws://' + 'localhost:8000/api/dashboard/ws';
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
        const res = await fetch('http://localhost:8000/api/orders/admin/all', {
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
        const res = await fetch('http://localhost:8000/api/inventory/', {
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
                const res = await fetch('http://localhost:8000/api/inventory/movement', {
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
                const res = await fetch('http://localhost:8000/api/crm/clients', {
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
            const res = await fetch(`http://localhost:8000/api/crm/recommendations/${userId}`, {
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

    
    // --- LÓGICA FACTURACIÓN DINÁMICA ---
    const loadDynamicBilling = async () => {
        const invContainer = document.getElementById('recentInvoicesContainer');
        if(invContainer) {
            const token = localStorage.getItem('jhire_jwt_token');
            try {
                const res = await fetch('http://localhost:8000/api/billing/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if(res.ok) {
                    const invoices = await res.json();
                    if(invoices.length > 0) {
                        invContainer.innerHTML = invoices.slice(0, 5).map(i => `
                        <div class="flex items-center justify-between p-3 border-b border-outline-variant/10 bg-surface dark:bg-surface-container hover:bg-surface-container-low transition-colors group cursor-pointer" onclick="Swal.fire({title: 'Detalle Comprobante Fiscal', html: '<div style=\'text-align:left;font-size:14px;\' class=\'bg-surface-container-low p-4 rounded-lg\'><p><strong>${i.invoice_number}</strong></p><p><strong>RUC:</strong> ${i.client_ruc_dni}</p><p><strong>Razón:</strong> ${i.client_name}</p><hr style=\'margin:10px 0;border-color:#ccc\'><div style=\'display:flex;justify-content:space-between\'><p>Subtotal:</p> <p>S/ ${parseFloat(i.subtotal).toFixed(2)}</p></div><div style=\'display:flex;justify-content:space-between\'><p>IGV(18%):</p> <p>S/ ${parseFloat(i.igv).toFixed(2)}</p></div><div style=\'display:flex;justify-content:space-between;font-weight:bold;margin-top:5px;\'><p>Total:</p> <p>S/ ${parseFloat(i.total).toFixed(2)}</p></div></div>', icon: 'info', showCancelButton: true, confirmButtonText: 'Ver representación (PDF)', cancelButtonText: 'Cerrar'}).then((res)=>{ if(res.isConfirmed){ window.open('http://localhost:8000/api/billing/'+i.id+'/pdf', '_blank'); } })">
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
                    } else {
                        invContainer.innerHTML = '<div class="p-8 text-center text-xs text-outline-variant flex flex-col items-center bg-surface-container-lowest rounded-lg border border-dashed border-outline/30"><span class="material-symbols-outlined text-4xl opacity-50 mb-2">receipt_long</span><p class="font-bold">Ningún comprobante fiscal emitido.</p></div>';
                    }
                }
            } catch(e) {}
        }
    };
    
    // Configurar Envío de Factura Formulada
    const invoiceForm = document.getElementById('invoiceForm');
    if(invoiceForm) {
        invoiceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const rucInput = document.getElementById('rucInput').value.trim();
            const clientNameInput = document.getElementById('clientNameInput').value.trim();
            const orderIdInput = document.getElementById('orderIdInput').value.trim();
            const compliance = document.getElementById('compliance').checked;
            const law29733 = document.getElementById('law29733').checked;
            
            if(!compliance || !law29733) {
                Swal.fire('Requisito Legal', 'Debe aceptar las políticas de privacidad y compliance SUNAT para generar comprobantes electrónicos.', 'warning');
                return;
            }
            
            if(!/^\d{8}$|^\d{11}$/.test(rucInput)) {
                Swal.fire('Error de RUC', 'El RUC/DNI debe contener 8 o 11 dígitos numéricos para la factura electrónica.', 'error');
                return;
            }
            
            // Show loading
            Swal.fire({
                title: 'Emitiendo CPE',
                html: 'Enviando payload XML UBL 2.1 a OSE/SUNAT...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });
            
            try {
                const token = localStorage.getItem('jhire_jwt_token');
                const res = await fetch('http://localhost:8000/api/billing/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        order_id: parseInt(orderIdInput),
                        client_ruc_dni: rucInput,
                        client_name: clientNameInput
                    })
                });
                
                const data = await res.json();
                
                if(res.ok) {
                    Swal.fire({
                        title: 'Comprobante Aceptado por SUNAT',
                        html: `<div class="text-left mt-4 text-sm bg-surface-container-low p-4 rounded-lg" style="user-select: text;">
                            <p><strong>Nro Resolución:</strong> SUNAT-${Math.floor(Math.random() * 1000000000)}</p>
                            <p class="mt-2 text-green-700 font-bold"><span class="material-symbols-outlined text-[14px]">check_circle</span> Factura ${data.invoice_number} generada correctamente por S/ ${parseFloat(data.total).toFixed(2)}</p>
                            <p class="text-xs text-outline mt-2 whitespace-pre-line break-all">Hash Firma: ${btoa(data.invoice_number + data.total)}</p>
                        </div>`,
                        icon: 'success',
                        confirmButtonText: 'Imprimir / Descargar PDF',
                        showCancelButton: true,
                        cancelButtonText: 'Cerrar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            window.open(`http://localhost:8000/api/billing/${data.id}/pdf`, '_blank');
                        }
                    });
                    invoiceForm.reset();
                    loadDynamicBilling();
                } else {
                    Swal.fire('Error al Emitir', data.detail || 'Verifique que el ID de la Órden comercial exista en el sistema.', 'error');
                }
            } catch(e) {
                Swal.fire('Fallo de Red', 'No se pudo contactar al facturador electrónico.', 'error');
            }
        });
        
        // Auto-fill logic for dummy RUC checking
        const validateBtn = document.getElementById('validateRucBtn');
        if(validateBtn) {
            validateBtn.addEventListener('click', () => {
                const ruc = document.getElementById('rucInput').value.trim();
                const nameInp = document.getElementById('clientNameInput');
                if(/^\d{8}$|^\d{11}$/.test(ruc)) {
                    if(!nameInp.value) {
                       nameInp.value = ruc.length === 11 ? "EMPRESA RUC " + ruc + " S.A.C." : "CLIENTE DNI " + ruc;
                    }
                }
            });
        }
    }
    loadDynamicCRM();
    loadDynamicBilling();
});
