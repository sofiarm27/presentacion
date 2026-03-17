// ============================================================
// CLIENTE HTTP CENTRALIZADO - src/services/api.js
// Todas las llamadas al backend pasan por este archivo.
// Usa fetch nativo de JavaScript (no se necesita Axios).
// Automáticamente agrega el token JWT en cada petición.
// ============================================================

// URL base del backend FastAPI (siempre en el puerto 8000)
// En producción, VITE_API_URL vendrá de Railway. En local, usará por defecto localhost:8000
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = {

  // -------------------------------------------------------
  // LOGIN: único endpoint que no necesita token previo
  // Envía correo y contraseña como formulario (no JSON)
  // porque FastAPI/OAuth2 así lo requiere en /token
  // -------------------------------------------------------
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);  // Correo del usuario
    formData.append('password', password);  // Contraseña

    const response = await fetch(`${API_URL}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',  // Formato de formulario, no JSON
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al iniciar sesión');
    }

    return response.json();  // Retorna { access_token, token_type }
  },

  // -------------------------------------------------------
  // FUNCIÓN CENTRAL DE PETICIONES
  // Todas las demás funciones del API usan esta.
  // Agrega automáticamente el JWT del localStorage.
  // Maneja los errores HTTP de forma centralizada.
  // -------------------------------------------------------
  async request(endpoint, options = {}) {
    // Leer el token JWT guardado al hacer login
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,  // Permite sobreescribir headers si se necesita
    };

    // Agregar el token de autenticación si existe
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // Si el token expiró o es inválido → cerrar sesión y redirigir al login
    if (response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }

    // Respuesta 204 (No Content) no tiene cuerpo → no llamar .json()
    if (response.status === 204) {
      return null;
    }

    // Manejar errores HTTP (400, 403, 404, 500, etc.)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error en la petición' }));
      // Pydantic (FastAPI) devuelve errores de validación como array de objetos
      if (Array.isArray(errorData.detail)) {
        const messages = errorData.detail.map(err => err.msg || err.message || JSON.stringify(err));
        throw new Error(messages.join('. '));
      }
      throw new Error(errorData.detail || 'Error en la petición');
    }

    return response.json();  // Parsear y retornar el JSON de la respuesta
  },

  // -------------------------------------------------------
  // MÉTODOS HTTP SIMPLIFICADOS
  // Wrappers de request() para cada método HTTP
  // -------------------------------------------------------

  // GET: obtener datos (no envía body)
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  // POST: crear nuevos recursos (envía body JSON)
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // PUT: actualizar recursos existentes (envía body JSON)
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // DELETE: eliminar recursos (no envía body)
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  // -------------------------------------------------------
  // MÉTODOS ESPECÍFICOS DEL MÓDULO DE BIBLIOTECA LEGAL
  // Encapsulan las rutas exactas del backend
  // -------------------------------------------------------

  // Obtiene todas las cláusulas de la biblioteca
  getClausulas() {
    return this.get('/contracts/clausulas');
  },

  // Obtiene todas las plantillas de la biblioteca
  getPlantillas() {
    return this.get('/contracts/plantillas');
  },

  // Crea una nueva cláusula en la biblioteca
  createClausula(data) {
    return this.post('/contracts/clausula', data);
  },

  // Crea una nueva plantilla en la biblioteca
  createPlantilla(data) {
    return this.post('/contracts/plantilla', data);
  },

  // Actualiza una cláusula existente por su ID
  updateClausula(id, data) {
    return this.put(`/contracts/clausula/${id}`, data);
  },

  // Actualiza una plantilla existente por su ID
  updatePlantilla(id, data) {
    return this.put(`/contracts/plantilla/${id}`, data);
  },

  // Obtiene un contrato específico por su ID (ej: CNT-2025-001)
  getContract(id) {
    return this.get(`/contracts/${id}`);
  },

  // Obtiene la lista de abogados disponibles para asignar a contratos
  getAbogados() {
    return this.get('/users/abogados');
  },

  // Obtiene todos los clientes registrados en el sistema
  getClients() {
    return this.get('/clients/');
  },
};

export default api;
