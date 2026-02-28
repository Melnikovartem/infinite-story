"""Tests for scene counter and progress tracking models."""

import pytest
import time
from datetime import datetime, UTC, timedelta
from app.models.scene_counter import SceneCounter


class TestSceneCounterModel:
    """Test SceneCounter model."""
    
    def test_creation(self):
        """Test creating a scene counter."""
        counter = SceneCounter(scene_number=1, total_visited=1)
        assert counter.scene_number == 1
        assert counter.total_visited == 1
        assert counter.elapsed_seconds >= 0
    
    def test_scene_number_validation(self):
        """Test that scene_number must be >= 1."""
        with pytest.raises(ValueError):
            SceneCounter(scene_number=0, total_visited=1)
    
    def test_update_elapsed(self):
        """Test updating elapsed time."""
        counter = SceneCounter(
            scene_number=1,
            total_visited=1,
            start_time=datetime.now(UTC) - timedelta(seconds=5)
        )
        
        elapsed = counter.update_elapsed()
        assert elapsed >= 5
    
    def test_get_elapsed_formatted(self):
        """Test formatting elapsed time."""
        counter = SceneCounter(
            scene_number=1,
            total_visited=1,
            start_time=datetime.now(UTC) - timedelta(hours=2, minutes=15, seconds=30)
        )
        
        formatted = counter.get_elapsed_formatted()
        assert "h" in formatted or "m" in formatted or "s" in formatted
        assert len(formatted) > 0
    
    def test_reading_pace(self):
        """Test reading pace calculation."""
        counter = SceneCounter(
            scene_number=5,
            total_visited=5,
            start_time=datetime.now(UTC) - timedelta(minutes=10),
            elapsed_seconds=600  # 10 minutes
        )
        
        pace = counter.get_reading_pace()
        # 10 minutes / 5 scenes = 2 minutes per scene
        assert pace == pytest.approx(2.0, abs=0.1)
    
    def test_reading_pace_calculation(self):
        """Test reading pace calculation with multiple visits."""
        counter = SceneCounter(
            scene_number=3,
            total_visited=3,
            start_time=datetime.now(UTC) - timedelta(minutes=5)
        )
        pace = counter.get_reading_pace()
        # Should be approximately 5 minutes / 3 = 1.67 minutes per scene
        assert pace == pytest.approx(1.67, abs=0.2)
    
    def test_estimate_remaining_time(self):
        """Test estimating remaining time."""
        counter = SceneCounter(
            scene_number=5,
            total_visited=5,
            start_time=datetime.now(UTC) - timedelta(minutes=10),
            elapsed_seconds=600  # 10 minutes for 5 scenes
        )
        
        # Estimate for 10 total scenes: 5 more scenes × 2 min/scene = 10 minutes
        remaining = counter.estimate_remaining_time(estimated_total_scenes=10)
        assert remaining is not None
        assert remaining > 0
    
    def test_estimate_remaining_time_already_done(self):
        """Test estimating remaining time when already done."""
        counter = SceneCounter(
            scene_number=10,
            total_visited=10,
            elapsed_seconds=600
        )
        
        remaining = counter.estimate_remaining_time(estimated_total_scenes=10)
        assert remaining is None
    
    def test_estimate_remaining_time_no_estimate(self):
        """Test estimating remaining time without total."""
        counter = SceneCounter(scene_number=1, total_visited=1)
        remaining = counter.estimate_remaining_time()
        assert remaining is None
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        counter = SceneCounter(scene_number=3, total_visited=3)
        data = counter.to_dict()
        
        assert isinstance(data, dict)
        assert data["scene_number"] == 3
        assert data["total_visited"] == 3
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "scene_number": 2,
            "total_visited": 2,
            "elapsed_seconds": 120,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        counter = SceneCounter.from_dict(data)
        assert counter.scene_number == 2
        assert counter.total_visited == 2
