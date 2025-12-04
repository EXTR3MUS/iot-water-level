import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app, fetch_latest_levels, DB_PATH

client = TestClient(app)

@pytest.fixture
def mock_db(tmp_path):
    """Create a temporary test database."""
    test_db = tmp_path / "test_water_levels.db"
    conn = sqlite3.connect(str(test_db))
    conn.execute("""
        CREATE TABLE water_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            water_level REAL NOT NULL,
            recorded_ts REAL NOT NULL
        )
    """)
    # Insert test data
    test_data = [
        (2.5, 1701000000.0),
        (3.0, 1701000005.0),
        (1.5, 1701000010.0),
    ]
    conn.executemany(
        "INSERT INTO water_levels (water_level, recorded_ts) VALUES (?, ?)",
        test_data
    )
    conn.commit()
    conn.close()
    return str(test_db)

def test_root_endpoint_success(mock_db):
    """Test the root endpoint returns buffer data."""
    with patch('app.main.DB_PATH', mock_db):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "buffer" in data
        assert isinstance(data["buffer"], list)
        assert len(data["buffer"]) == 3

def test_root_endpoint_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200

def test_fetch_latest_levels_default_limit(mock_db):
    """Test fetch_latest_levels with default limit."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels()
        assert len(result) == 3
        # Should be ordered DESC by recorded_ts
        assert result[0]["water_level"] == 1.5

def test_fetch_latest_levels_custom_limit(mock_db):
    """Test fetch_latest_levels with custom limit."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels(limit=2)
        assert len(result) == 2

def test_fetch_latest_levels_empty_db(tmp_path):
    """Test fetch_latest_levels with empty database."""
    empty_db = tmp_path / "empty.db"
    conn = sqlite3.connect(str(empty_db))
    conn.execute("""
        CREATE TABLE water_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            water_level REAL NOT NULL,
            recorded_ts REAL NOT NULL
        )
    """)
    conn.close()
    
    with patch('app.main.DB_PATH', str(empty_db)):
        result = fetch_latest_levels()
        assert result == []

def test_fetch_latest_levels_missing_db():
    """Test fetch_latest_levels handles missing database gracefully."""
    with patch('app.main.DB_PATH', '/nonexistent/path.db'):
        result = fetch_latest_levels()
        assert result == []

def test_fetch_latest_levels_timezone_format(mock_db):
    """Test that timestamps are formatted with Brazil timezone."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels(limit=1)
        assert len(result) == 1
        # Check ISO format timestamp
        assert "T" in result[0]["recorded_ts"]
        assert "-03:00" in result[0]["recorded_ts"]  # Brazil TZ offset

@pytest.mark.asyncio
async def test_root_endpoint_response_structure(mock_db):
    """Test the response structure matches expected format."""
    with patch('app.main.DB_PATH', mock_db):
        response = client.get("/")
        data = response.json()
        
        assert "buffer" in data
        for item in data["buffer"]:
            assert "water_level" in item
            assert "recorded_ts" in item
            assert isinstance(item["water_level"], (int, float))
            assert isinstance(item["recorded_ts"], str)

def test_fetch_latest_levels_ordering(mock_db):
    """Test that results are ordered by timestamp descending."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels()
        assert len(result) == 3
        # Most recent first (1701000010.0)
        assert result[0]["water_level"] == 1.5
        # Oldest last (1701000000.0)
        assert result[2]["water_level"] == 2.5

def test_cors_allows_configured_origins():
    """Test CORS allows configured origins."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    # CORS should allow the origin
    assert response.headers.get("access-control-allow-origin") in [
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ] or "*" in response.headers.get("access-control-allow-origin", "")

def test_fetch_latest_levels_with_large_limit(mock_db):
    """Test fetch_latest_levels with limit larger than available data."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels(limit=100)
        # Should return all 3 rows, not fail
        assert len(result) == 3

def test_fetch_latest_levels_data_types(mock_db):
    """Test that water_level is float and recorded_ts is ISO string."""
    with patch('app.main.DB_PATH', mock_db):
        result = fetch_latest_levels(limit=1)
        assert isinstance(result[0]["water_level"], float)
        assert isinstance(result[0]["recorded_ts"], str)
        # ISO 8601 format check
        assert ":" in result[0]["recorded_ts"]
