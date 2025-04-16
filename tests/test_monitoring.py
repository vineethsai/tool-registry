import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import time
from uuid import UUID

from tool_registry.core.monitoring import monitoring, monitor_request, log_access

@pytest.fixture
def mock_counter():
    """Mock a Prometheus counter."""
    counter = MagicMock()
    labels = MagicMock()
    counter.labels.return_value = labels
    return counter, labels

@pytest.fixture
def mock_histogram():
    """Mock a Prometheus histogram."""
    histogram = MagicMock()
    labels = MagicMock()
    timer_ctx = MagicMock()
    labels.time.return_value = timer_ctx
    histogram.labels.return_value = labels
    return histogram, labels, timer_ctx

def test_monitoring_init():
    """Test monitoring initialization."""
    test_monitoring = monitoring.__class__(prometheus_port=9090)
    assert test_monitoring.prometheus_port == 9090

@patch('tool_registry.core.monitoring.start_http_server')
def test_monitoring_start(mock_start_server):
    """Test starting the monitoring server."""
    test_monitoring = monitoring.__class__(prometheus_port=9090)
    test_monitoring.start()
    mock_start_server.assert_called_once_with(9090)

def test_log_request(mock_counter):
    """Test logging a request."""
    counter, labels = mock_counter
    
    with patch('tool_registry.core.monitoring.REQUEST_COUNT', counter):
        monitoring.log_request('/test', 'GET', 200)
        
    counter.labels.assert_called_once_with(endpoint='/test', method='GET', status=200)
    labels.inc.assert_called_once()

def test_log_error(mock_counter):
    """Test logging an error."""
    counter, labels = mock_counter
    
    with patch('tool_registry.core.monitoring.ERROR_COUNT', counter):
        with patch('tool_registry.core.monitoring.logger.error') as mock_logger:
            monitoring.log_error('/test', 'GET', 'TestError')
            
    counter.labels.assert_called_once_with(endpoint='/test', method='GET', error_type='TestError')
    labels.inc.assert_called_once()
    mock_logger.assert_called_once()

def test_measure_latency(mock_histogram):
    """Test measuring request latency."""
    histogram, labels, timer_ctx = mock_histogram
    
    with patch('tool_registry.core.monitoring.REQUEST_LATENCY', histogram):
        result = monitoring.measure_latency('/test', 'GET')
        
    histogram.labels.assert_called_once_with(endpoint='/test', method='GET')
    labels.time.assert_called_once()
    assert result == timer_ctx

@pytest.mark.asyncio
async def test_monitor_request_decorator_success():
    """Test the monitor_request decorator with a successful function."""
    # Define a test function
    @monitor_request
    async def test_function():
        return "success"
    
    # Patch the monitoring components
    with patch('tool_registry.core.monitoring.monitoring.log_request') as mock_log_request:
        with patch('tool_registry.core.monitoring.logger.info') as mock_logger:
            # Call the decorated function
            result = await test_function()
            
    # Verify the function executed correctly
    assert result == "success"
    
    # Verify monitoring was called
    mock_log_request.assert_called_once()
    mock_logger.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_request_decorator_with_params():
    """Test the monitor_request decorator with parameters."""
    # Define a test function with custom endpoint
    @monitor_request(endpoint='/custom')
    async def test_function():
        return "success"
    
    # Patch the monitoring components
    with patch('tool_registry.core.monitoring.monitoring.log_request') as mock_log_request:
        with patch('tool_registry.core.monitoring.logger.info') as mock_logger:
            # Call the decorated function
            result = await test_function()
            
    # Verify the function executed correctly
    assert result == "success"
    
    # Verify monitoring was called with custom endpoint
    mock_log_request.assert_called_once_with('/custom', 'TEST_FUNCTION', 200)
    mock_logger.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_request_decorator_exception():
    """Test the monitor_request decorator with a function that raises an exception."""
    # Define a test function that raises an exception
    @monitor_request
    async def test_function():
        raise ValueError("Test exception")
    
    # Patch the monitoring components
    with patch('tool_registry.core.monitoring.monitoring.log_request') as mock_log_request:
        with patch('tool_registry.core.monitoring.monitoring.log_error') as mock_log_error:
            with patch('tool_registry.core.monitoring.logger.info') as mock_logger:
                # Call the decorated function and expect an exception
                with pytest.raises(ValueError, match="Test exception"):
                    await test_function()
                    
    # Verify monitoring was called
    mock_log_error.assert_called_once()
    mock_log_request.assert_called_once_with('test_function', 'TEST_FUNCTION', 500)
    mock_logger.assert_called_once()

@pytest.mark.asyncio
async def test_log_access():
    """Test the log_access function."""
    agent_id = UUID("00000000-0000-0000-0000-000000000001")
    tool_id = "00000000-0000-0000-0000-000000000002"
    action = "TEST_ACTION"
    status = "GRANTED"
    details = {"reason": "Test reason"}
    
    with patch('tool_registry.core.monitoring.logger.info') as mock_logger:
        with patch('tool_registry.core.monitoring.monitoring.log_request') as mock_log_request:
            await log_access(agent_id, tool_id, action, status, details)
            
    # Verify logging was called
    mock_logger.assert_called_once()
    
    # Verify the right endpoints were called based on status
    mock_log_request.assert_called_once_with(f"/tools/{tool_id}/access", "POST", 200)
    
    # Test with denied status
    with patch('tool_registry.core.monitoring.logger.info') as mock_logger:
        with patch('tool_registry.core.monitoring.monitoring.log_request') as mock_log_request:
            await log_access(agent_id, tool_id, action, "DENIED")
            
    mock_log_request.assert_called_once_with(f"/tools/{tool_id}/access", "POST", 403) 