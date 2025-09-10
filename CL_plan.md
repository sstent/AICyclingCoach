### Phase 5: Testing and Deployment (Week 12-13)

#### Week 12: Testing
1. **Backend Testing**
   - Implement comprehensive unit tests for critical services:
     - Garmin sync service (mock API responses)
     - AI service (mock OpenRouter API)
     - Workflow services (plan generation, evolution)
   - API endpoint testing with realistic payloads
   - Error handling and edge case testing
   - Database operation tests (including rollback scenarios)

   Example test for Garmin service:
   ```python
   # tests/test_garmin_service.py
   import pytest
   from unittest.mock import AsyncMock, patch
   from app.services.garmin import GarminService
   from app.exceptions import GarminAuthError

   @pytest.mark.asyncio
   async def test_garmin_auth_failure():
       with patch('garth.Client', side_effect=Exception("Auth failed")):
           service = GarminService()
           with pytest.raises(GarminAuthError):
               await service.authenticate()
   ```

2. **Integration Testing**
   - Test full Garmin sync workflow: authentication → activity fetch → storage
   - Verify AI analysis pipeline: workout → analysis → plan evolution
   - Database transaction tests across multiple operations
   - File system integration tests (GPX upload/download)

3. **Frontend Testing**
   - Component tests using React Testing Library
   - User workflow tests (upload GPX → generate plan → analyze workout)
   - API response handling and error display tests
   - Responsive design verification across devices

   Example component test:
   ```javascript
   // frontend/src/components/__tests__/GarminSync.test.jsx
   import { render, screen, fireEvent } from '@testing-library/react';
   import GarminSync from '../GarminSync';

   test('shows sync status after triggering', async () => {
       render(<GarminSync />);
       fireEvent.click(screen.getByText('Sync Recent Activities'));
       expect(await screen.findByText('Syncing...')).toBeInTheDocument();
   });
   ```

4. **Continuous Integration Setup**
   - Configure GitHub Actions pipeline:
     - Backend test suite (Python)
     - Frontend test suite (Jest)
     - Security scanning (dependencies, secrets)
     - Docker image builds on successful tests
   - Automated database migration checks
   - Test coverage reporting

#### Week 13: Deployment Preparation
1. **Environment Configuration**
   ```bash
   # .env.production
   GARMIN_USERNAME=your_garmin_email
   GARMIN_PASSWORD=your_garmin_password
   OPENROUTER_API_KEY=your_openrouter_key
   AI_MODEL=anthropic/claude-3-sonnet-20240229
   API_KEY=your_secure_api_key
   ```

2. **Production Docker Setup**
   - Optimize Dockerfiles for production:
     - Multi-stage builds
     - Minimized image sizes
     - Proper user permissions
   - Health checks for all services
   - Resource limits in docker-compose.prod.yml

3. **Backup Strategy**
   - Implement daily automated backups:
     - Database (pg_dump)
     - GPX files
     - Garmin sessions
   - Backup rotation (keep last 30 days)
   - Verify restore procedure

4. **Monitoring and Logging**
   - Structured logging with log rotation
   - System health dashboard
   - Error tracking and alerting
   - Performance monitoring

## Key Technical Decisions
...