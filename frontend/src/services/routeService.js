import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const api = axios.create({
  baseURL: '/api'
});

// Request interceptor to add API key header
api.interceptors.request.use(config => {
  const { apiKey } = useAuth.getState();
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const uploadRoute = async (formData) => {
  try {
    const response = await api.post('/routes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to upload route');
  }
};

export const getRouteDetails = async (routeId) => {
  try {
    const response = await api.get(`/routes/${routeId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to fetch route details');
  }
};

export const saveRouteMetadata = async (routeId, metadata) => {
  try {
    const response = await api.put(`/routes/${routeId}/metadata`, metadata);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to save metadata');
  }
};

export const saveRouteSections = async (routeId, sections) => {
  try {
    const response = await api.post(`/routes/${routeId}/sections`, { sections });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to save sections');
  }
};

export const deleteRoute = async (routeId) => {
  try {
    const response = await api.delete(`/routes/${routeId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to delete route');
  }
};