import axios from 'axios';

// Create axios instance
const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for Auth Token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const teachersApi = {
    getAll: () => api.get('/teachers/', { params: { limit: 5000 } }),
    create: (data: any) => api.post('/teachers/', data),
    update: (id: string, data: any) => api.put(`/teachers/${id}`, data),
    delete: (id: string) => api.delete(`/teachers/${id}`),
};

export const coursesApi = {
    getAll: () => api.get('/courses/', { params: { limit: 5000 } }),
    create: (data: any) => api.post('/courses/', data),
    update: (id: string, data: any) => api.put(`/courses/${id}`, data),
    delete: (id: string) => api.delete(`/courses/${id}`),
};

export const roomsApi = {
    getAll: () => api.get('/rooms/', { params: { limit: 5000 } }),
    create: (data: any) => api.post('/rooms/', data),
    update: (id: string, data: any) => api.put(`/rooms/${id}`, data),
    delete: (id: string) => api.delete(`/rooms/${id}`),
};

export const studentGroupsApi = {
    getAll: () => api.get('/student-groups/', { params: { limit: 5000 } }),
    create: (data: any) => api.post('/student-groups/', data),
    update: (id: string, data: any) => api.put(`/student-groups/${id}`, data),
    delete: (id: string) => api.delete(`/student-groups/${id}`),
};

export const breaksApi = {
    getAll: () => api.get('/breaks/', { params: { limit: 5000 } }),
    create: (data: any) => api.post('/breaks/', data),
    update: (id: string, data: any) => api.put(`/breaks/${id}`, data),
    delete: (id: string) => api.delete(`/breaks/${id}`),
};

export const solverApi = {
    generate: (term: string, config?: any) => api.post('/solver/generate', config, { params: { term } }),
    getStatus: (taskId: string) => api.get(`/solver/status/${taskId}`),
    getLogs: (taskId: string) => api.get(`/solver/logs/${taskId}`),
    getSaved: (term: string) => api.get(`/solver/timetable/${term}`),
};

export const importApi = {
    loadDistribution: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/imports/load-distribution', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    resetMasterData: () => api.delete('/imports/master-data'),
};

export const aiApi = {
    chat: (message: string, currentConfig: any, term = 'Fall 2025') => api.post('/ai/chat', { message, current_config: currentConfig, term }, { timeout: 30000 }),
    applyTimetableChange: (proposal: any) => api.post('/ai/apply-timetable-change', { proposal }, { timeout: 30000 }),
};

export default api;
