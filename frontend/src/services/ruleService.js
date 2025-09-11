import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL + '/rules';
const API_KEY = process.env.REACT_APP_API_KEY;

const apiClient = axios.create({
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

export const getRuleSets = async () => {
  try {
    const response = await apiClient.get(API_URL);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch rule sets');
  }
};

export const createRuleSet = async (ruleData) => {
  try {
    const response = await apiClient.post(API_URL, ruleData);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to create rule set');
  }
};

export const updateRuleSet = async (id, ruleData) => {
  try {
    const response = await apiClient.put(`${API_URL}/${id}`, ruleData);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to update rule set');
  }
};

export const deleteRuleSet = async (id) => {
  try {
    await apiClient.delete(`${API_URL}/${id}`);
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to delete rule set');
  }
};

export const parseRule = async (text) => {
  try {
    const response = await apiClient.post(`${API_URL}/parse`, { text });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to parse rules');
  }
};