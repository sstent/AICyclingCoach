import axios from 'axios';

export const generatePlan = async (apiKey, planData) => {
  try {
    const response = await axios.post('/api/plans/generate', planData, {
      headers: { 'X-API-Key': apiKey }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to generate plan');
  }
};

export const getPlanPreview = async (apiKey, planId) => {
  try {
    const response = await axios.get(`/api/plans/${planId}/preview`, {
      headers: { 'X-API-Key': apiKey }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to load plan preview');
  }
};

export const pollPlanStatus = async (apiKey, planId, interval = 2000) => {
  return new Promise(async (resolve, reject) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`/api/plans/${planId}/status`, {
          headers: { 'X-API-Key': apiKey }
        });
        
        if (response.data.status === 'completed') {
          resolve(response.data.plan);
        } else if (response.data.status === 'failed') {
          reject(new Error('Plan generation failed'));
        } else {
          setTimeout(checkStatus, interval);
        }
      } catch (error) {
        reject(error);
      }
    };

    await checkStatus();
  });
};