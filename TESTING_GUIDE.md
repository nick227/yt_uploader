# Testing Guide

This guide covers the comprehensive testing setup for the Media Uploader application, including unit tests, integration tests, and testing best practices.

## 🏗️ Testing Architecture

The testing framework is built around **pytest** with the following structure:

```
tests/
├── __init__.py              # Test package
├── conftest.py              # Shared fixtures and configuration
├── test_auth_manager.py     # Authentication manager tests
├── test_upload_manager.py   # Upload manager tests
├── test_youtube_service.py  # YouTube service tests
├── test_models.py           # Core models tests
└── test_ui/                 # UI component tests (future)
    ├── test_main_window.py
    ├── test_media_row.py
    └── test_auth_widget.py
```

## 🚀 Quick Start

### 1. Install Testing Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install testing dependencies only
pip install pytest pytest-cov pytest-mock pytest-qt
```

### 2. Run Tests

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py --type unit

# Run with coverage
python run_tests.py --type coverage

# Run quick tests (excluding slow tests)
python run_tests.py --type quick

# Run with verbose output
python run_tests.py --verbose

# Run in parallel
python run_tests.py --parallel 4
```

### 3. Direct pytest Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_manager.py

# Run specific test function
pytest tests/test_auth_manager.py::TestGoogleAuthManager::test_login_success

# Run tests with markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=app --cov=core --cov=services --cov=infra --cov-report=html
```

## 📋 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Test individual functions and methods in isolation
- **Speed**: Fast (< 100ms per test)
- **Dependencies**: Mocked external dependencies
- **Scope**: Single class or function

### Integration Tests (`@pytest.mark.integration`)
- **Purpose**: Test component interactions and workflows
- **Speed**: Medium (100ms - 1s per test)
- **Dependencies**: May use real external services
- **Scope**: Multiple components working together

### Authentication Tests (`@pytest.mark.auth`)
- **Purpose**: Test Google OAuth2 authentication flow
- **Speed**: Medium to slow
- **Dependencies**: Mocked Google APIs
- **Scope**: Authentication manager and related components

### Upload Tests (`@pytest.mark.upload`)
- **Purpose**: Test YouTube upload functionality
- **Speed**: Medium to slow
- **Dependencies**: Mocked YouTube API
- **Scope**: Upload manager and YouTube service

### UI Tests (`@pytest.mark.ui`)
- **Purpose**: Test UI components and user interactions
- **Speed**: Medium
- **Dependencies**: Qt application context
- **Scope**: UI widgets and user workflows

## 🧪 Test Fixtures

### Common Fixtures (in `conftest.py`)

```python
@pytest.fixture
def qt_app():
    """QApplication instance for Qt tests."""
    
@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    
@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager."""
    
@pytest.fixture
def mock_youtube_service():
    """Mock YouTube service."""
    
@pytest.fixture
def sample_media_files():
    """Sample media files for testing."""
```

### Using Fixtures

```python
def test_upload_with_mock_auth(mock_auth_manager, temp_dir):
    """Test upload with mocked authentication."""
    # Your test code here
    pass
```

## 🎯 Testing Best Practices

### 1. Test Structure (AAA Pattern)

```python
def test_function_name():
    """Test description."""
    # Arrange - Set up test data and mocks
    mock_service = Mock()
    test_data = {"key": "value"}
    
    # Act - Execute the function being tested
    result = function_under_test(mock_service, test_data)
    
    # Assert - Verify the results
    assert result == expected_value
    mock_service.method.assert_called_once_with(test_data)
```

### 2. Mocking External Dependencies

```python
@patch('module.external_service')
def test_with_external_service(mock_service):
    """Test with mocked external service."""
    mock_service.return_value.method.return_value = "mocked_result"
    
    result = function_under_test()
    assert result == "mocked_result"
```

### 3. Testing Error Conditions

```python
def test_function_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_under_test("invalid_input")
```

### 4. Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function_under_test()
    assert result == expected_value
```

## 🔧 Test Configuration

### pytest.ini Configuration

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
    --cov=app
    --cov=core
    --cov=services
    --cov=infra
    --cov-report=term-missing
    --cov-report=html:htmlcov

markers =
    unit: Unit tests
    integration: Integration tests
    auth: Authentication tests
    upload: Upload tests
    ui: UI tests
    slow: Slow tests
    mock: Mock tests
```

### Coverage Configuration

```ini
[coverage:run]
source = app,core,services,infra
omit = 
    */tests/*
    */__pycache__/*
    */migrations/*
    */venv/*
    */env/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

## 📊 Coverage Reports

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov=core --cov=services --cov=infra --cov-report=html

# View coverage in terminal
pytest --cov=app --cov=core --cov=services --cov=infra --cov-report=term-missing
```

### Coverage Targets

- **Overall Coverage**: > 90%
- **Core Modules**: > 95%
- **UI Components**: > 80%
- **Integration Tests**: > 85%

## 🚨 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        python run_tests.py --type unit --verbose
    
    - name: Generate coverage report
      run: |
        python run_tests.py --type coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## 🐛 Debugging Tests

### Debug Test Failures

```bash
# Run specific failing test with debug output
pytest tests/test_auth_manager.py::test_login_success -v -s

# Run with pdb debugger
pytest tests/test_auth_manager.py::test_login_success --pdb

# Run with detailed traceback
pytest tests/test_auth_manager.py::test_login_success --tb=long
```

### Debug Qt Tests

```python
def test_qt_component(qt_app):
    """Test Qt component with debug output."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Your Qt test code here
    widget = MyWidget()
    assert widget.isVisible()
```

## 📈 Performance Testing

### Benchmark Tests

```python
import time
import pytest

def test_performance():
    """Test function performance."""
    start_time = time.time()
    
    # Execute function
    result = function_under_test()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assert performance requirements
    assert execution_time < 1.0  # Should complete in under 1 second
    assert result == expected_value
```

### Memory Usage Tests

```python
import psutil
import os

def test_memory_usage():
    """Test memory usage of function."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Execute function
    result = function_under_test()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assert memory requirements (e.g., < 10MB increase)
    assert memory_increase < 10 * 1024 * 1024
```

## 🔍 Test Data Management

### Test Data Fixtures

```python
@pytest.fixture
def sample_video_files(temp_dir):
    """Create sample video files for testing."""
    files = []
    for i in range(3):
        file_path = temp_dir / f"test_video_{i}.mp4"
        file_path.write_bytes(b"fake video content")
        files.append(file_path)
    return files

@pytest.fixture
def sample_audio_files(temp_dir):
    """Create sample audio files for testing."""
    files = []
    for i in range(2):
        file_path = temp_dir / f"test_audio_{i}.mp3"
        file_path.write_bytes(b"fake audio content")
        files.append(file_path)
    return files
```

### Test Data Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_test_files(temp_dir):
    """Automatically cleanup test files after each test."""
    yield
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
```

## 📝 Writing New Tests

### Test File Template

```python
"""
Tests for [Module Name].
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from module.under_test import ClassUnderTest


class TestClassUnderTest:
    """Test the ClassUnderTest class."""
    
    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        return ClassUnderTest()
    
    def test_method_success(self, instance):
        """Test successful method execution."""
        # Arrange
        input_data = "test_input"
        
        # Act
        result = instance.method(input_data)
        
        # Assert
        assert result == "expected_output"
    
    def test_method_failure(self, instance):
        """Test method failure handling."""
        with pytest.raises(ValueError, match="Invalid input"):
            instance.method("invalid_input")
    
    @patch('module.external_service')
    def test_method_with_external_dependency(self, mock_service, instance):
        """Test method with external dependency."""
        mock_service.return_value.method.return_value = "mocked_result"
        
        result = instance.method_with_external_call()
        assert result == "mocked_result"
        mock_service.return_value.method.assert_called_once()
```

## 🎯 Test Maintenance

### Regular Tasks

1. **Weekly**: Run full test suite and check coverage
2. **Before Releases**: Run integration tests with real services
3. **Monthly**: Review and update test data
4. **Quarterly**: Audit test performance and optimize slow tests

### Test Review Checklist

- [ ] Tests cover all code paths
- [ ] Error conditions are tested
- [ ] Edge cases are covered
- [ ] Tests are fast and reliable
- [ ] Mock usage is appropriate
- [ ] Test names are descriptive
- [ ] Documentation is up to date

---

**Remember**: Good tests are the foundation of reliable software. Write tests first, keep them simple, and maintain them regularly.
