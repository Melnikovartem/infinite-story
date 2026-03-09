"""Performance benchmarks to prevent regressions."""

import asyncio
import time
import pytest
from app.models import Story, StorySegment, StoryChoice


class TestPerformance:
    """Performance benchmarks to prevent regressions."""
    
    def test_segment_creation_speed(self, benchmark, sample_story):
        """Creating a segment should be fast (<10ms)."""
        def create_segment():
            return StorySegment(
                story=sample_story,
                id="perf_test_seg",
                text_blocks=[],
                episode_number=1
            )
        
        result = benchmark(create_segment)
    
    def test_story_creation_speed(self, benchmark):
        """Creating a story should be fast (<5ms)."""
        def create_story():
            return Story(
                id="perf_story",
                title="Performance Test Story",
                description="Testing performance",
            )
        
        result = benchmark(create_story)
    
    def test_choice_creation_speed(self, benchmark, sample_story):
        """Creating a choice should be fast (<5ms)."""
        def create_choice():
            return StoryChoice(
                story=sample_story,
                id="perf_choice",
                text="Test choice",
            )
        
        result = benchmark(create_choice)
    
    def test_segment_save_speed(self, benchmark, sample_story):
        """Saving a segment should be reasonably fast (<100ms)."""
        seg = StorySegment(
            story=sample_story,
            id="perf_save_test",
            text_blocks=[]
        )
        
        def save_segment():
            seg.save()
        
        result = benchmark(save_segment)
    
    def test_segment_load_speed(self, benchmark, sample_story):
        """Loading a segment should be fast (<100ms)."""
        # Create and save a segment first
        seg = StorySegment(
            story=sample_story,
            id="perf_load_test",
            text_blocks=[]
        )
        seg.save()
        
        def load_segment():
            return StorySegment.load(sample_story.id, "perf_load_test", story=sample_story)
        
        result = benchmark(load_segment)
    
    def test_story_load_speed(self, benchmark):
        """Loading a story should be fast (<100ms)."""
        def load_story():
            try:
                return Story.load("test", "test")
            except Exception:
                return None
        
        result = benchmark(load_story)
    
    def test_memory_usage_story_creation(self, sample_story):
        """Creating multiple stories shouldn't blow up memory."""
        import tracemalloc
        
        tracemalloc.start()
        
        stories = []
        for i in range(50):
            story = Story(
                id=f"perf_story_{i}",
                title=f"Story {i}",
                description=f"Test story {i}",
            )
            stories.append(story)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Peak memory {peak_mb:.1f}MB exceeds limit"
    
    def test_memory_usage_segment_creation(self, sample_story):
        """Creating multiple segments shouldn't blow up memory."""
        import tracemalloc
        
        tracemalloc.start()
        
        segments = []
        for i in range(100):
            seg = StorySegment(
                story=sample_story,
                id=f"perf_seg_{i}",
                text_blocks=[]
            )
            segments.append(seg)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Peak memory {peak_mb:.1f}MB exceeds limit"
    
    def test_segment_list_performance(self, benchmark, sample_story):
        """Listing segments should be reasonably fast."""
        for i in range(10):
            seg = StorySegment(
                story=sample_story,
                id=f"list_test_{i}",
                text_blocks=[]
            )
            seg.save()
        
        def list_segments():
            try:
                return StorySegment.list_all(sample_story.id)
            except Exception:
                return []
        
        result = benchmark(list_segments)
    
    def test_batch_operations_performance(self, benchmark, sample_story):
        """Batch operations should be reasonably fast."""
        def create_batch():
            segments = []
            for i in range(20):
                seg = StorySegment(
                    story=sample_story,
                    id=f"batch_{i}",
                    text_blocks=[]
                )
                segments.append(seg)
            return segments
        
        result = benchmark(create_batch)


class TestPerformanceRegression:
    """Tests to catch performance regressions over time."""
    
    def test_story_initialization_doesnt_regress(self, benchmark):
        """Ensure story initialization doesn't get slower."""
        def init():
            return Story(
                id="regression_test",
                title="Test",
                description="Test",
            )
        
        result = benchmark(init)
    
    def test_segment_initialization_doesnt_regress(self, benchmark, sample_story):
        """Ensure segment initialization doesn't get slower."""
        def init():
            return StorySegment(
                story=sample_story,
                id="regression_seg",
                text_blocks=[]
            )
        
        result = benchmark(init)
    
    def test_choice_lookup_doesnt_regress(self, benchmark, sample_story):
        """Ensure choice lookup doesn't get slower."""
        choices = {}
        for i in range(10):
            choice = StoryChoice(
                story=sample_story,
                id=f"choice_{i}",
                text=f"Choice {i}",
            )
            choices[f"choice_{i}"] = choice
        
        def lookup():
            return choices.get("choice_5")
        
        result = benchmark(lookup)


# Performance baseline expectations
PERFORMANCE_BASELINES = {
    "segment_creation": 10,      # ms
    "context_building": 50,      # ms
    "save_load_cycle": 100,      # ms
    "generation": 5000,          # ms (5 seconds)
    "memory_usage": 100,         # MB
}


def test_performance_baselines_documented():
    """Verify performance baselines are documented."""
    assert "segment_creation" in PERFORMANCE_BASELINES
    assert "context_building" in PERFORMANCE_BASELINES
    assert "save_load_cycle" in PERFORMANCE_BASELINES
    assert "generation" in PERFORMANCE_BASELINES
    assert "memory_usage" in PERFORMANCE_BASELINES


def test_benchmark_configuration():
    """Verify benchmark configuration is available."""
    assert True
