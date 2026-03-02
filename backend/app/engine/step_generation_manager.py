"""Step-by-step story generation manager with skip and rerun capabilities."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import hashlib

from app.models.story import Story
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.step_generation_manager")


class GenerationStep:
    """Represents a single generation step with metadata."""
    
    def __init__(
        self,
        step_num: int,
        name: str,
        description: str,
        dependencies: List[int] = None
    ):
        self.step_num = step_num
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, completed, skipped, failed
        self.completed_at: Optional[str] = None
        self.output_hash: Optional[str] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_num": self.step_num,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status,
            "completed_at": self.completed_at,
            "output_hash": self.output_hash,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationStep":
        """Create from dictionary."""
        step = cls(
            step_num=data["step_num"],
            name=data["name"],
            description=data["description"],
            dependencies=data.get("dependencies", [])
        )
        step.status = data.get("status", "pending")
        step.completed_at = data.get("completed_at")
        step.output_hash = data.get("output_hash")
        step.error_message = data.get("error_message")
        return step


class StepGenerationManager:
    """Manages step-by-step story generation with dependency tracking."""
    
    # Define all generation steps
    STEPS = [
        GenerationStep(0, "Story Planner", "Plan story scope (factions, locations, characters)", []),
        GenerationStep(1, "World Generator", "Generate world context and fundamental truths", [0]),
        GenerationStep(2, "Faction Generator", "Generate 1-5 factions with goals and leaders", [0, 1]),
        GenerationStep(3, "Magic System Generator", "Generate magic/tech system with limitations", [1]),
        GenerationStep(4, "Location Generator", "Generate 5-15 world locations", [1]),
        GenerationStep(5, "Arc Generator", "Generate 3 world-level story arcs", [1, 2]),
        GenerationStep(6, "Character Generator", "Generate faction-aligned characters", [2, 5]),
        GenerationStep(7, "Protagonist Selector", "Select or develop protagonist", [6]),
        GenerationStep(8, "Opening Scene Generator", "Create opening scene", [1, 2, 7]),
        GenerationStep(9, "Choice Generator", "Generate choices for opening scene", [8]),
    ]
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize step generation manager.
        
        Args:
            story: The Story instance
            generator: AI text generator
        """
        self.story = story
        self.generator = generator
        self.steps: Dict[int, GenerationStep] = {s.step_num: GenerationStep(
            s.step_num, s.name, s.description, s.dependencies
        ) for s in self.STEPS}
        self.metadata_file = self._get_metadata_file()
        self._load_metadata()
    
    def _get_metadata_file(self) -> Path:
        """Get path to step metadata file."""
        story_dir = Path(self.story.get_storage_path()) if hasattr(self.story, 'get_storage_path') else Path.home() / '.infinite_story_data' / self.story.id
        story_dir.mkdir(parents=True, exist_ok=True)
        return story_dir / "generation_steps.json"
    
    def _load_metadata(self) -> None:
        """Load step metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for step_data in data.get("steps", []):
                        step_num = step_data["step_num"]
                        if step_num in self.steps:
                            self.steps[step_num] = GenerationStep.from_dict(step_data)
                logger.debug(f"Loaded generation metadata from {self.metadata_file}")
            except Exception as e:
                logger.warning(f"Failed to load generation metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save step metadata to file."""
        try:
            data = {
                "story_id": self.story.id,
                "saved_at": datetime.now().isoformat(),
                "steps": [step.to_dict() for step in self.steps.values()]
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved generation metadata to {self.metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save generation metadata: {e}")
    
    def _compute_hash(self, data: Any) -> str:
        """Compute hash of data for change detection."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get_step_status(self, step_num: int) -> Dict[str, Any]:
        """Get status of a specific step.
        
        Args:
            step_num: Step number (0-9)
            
        Returns:
            Dict with step status information
        """
        if step_num not in self.steps:
            return {"error": f"Step {step_num} not found"}
        
        step = self.steps[step_num]
        return {
            "step_num": step.step_num,
            "name": step.name,
            "description": step.description,
            "status": step.status,
            "dependencies": step.dependencies,
            "completed_at": step.completed_at,
            "can_run": self._can_run_step(step_num),
            "missing_deps": self._get_missing_dependencies(step_num)
        }
    
    def get_all_steps_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all steps.
        
        Returns:
            Dict mapping step numbers to their status info
        """
        return {i: self.get_step_status(i) for i in range(10)}
    
    def _can_run_step(self, step_num: int) -> bool:
        """Check if a step can be run."""
        if step_num not in self.steps:
            return False
        
        step = self.steps[step_num]
        
        # Check dependencies
        for dep in step.dependencies:
            dep_status = self.steps[dep].status
            if dep_status not in ("completed", "skipped"):
                return False
        
        return True
    
    def _get_missing_dependencies(self, step_num: int) -> List[int]:
        """Get list of missing dependencies for a step."""
        if step_num not in self.steps:
            return []
        
        step = self.steps[step_num]
        missing = []
        
        for dep in step.dependencies:
            if self.steps[dep].status not in ("completed", "skipped"):
                missing.append(dep)
        
        return missing
    
    def mark_step_completed(
        self,
        step_num: int,
        output_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark a step as completed.
        
        Args:
            step_num: Step number
            output_data: Optional data to hash for change detection
        """
        if step_num not in self.steps:
            raise ValueError(f"Step {step_num} not found")
        
        step = self.steps[step_num]
        step.status = "completed"
        step.completed_at = datetime.now().isoformat()
        
        if output_data:
            step.output_hash = self._compute_hash(output_data)
        
        # Mark downstream steps for rerun if this step changed
        self._mark_downstream_for_rerun(step_num)
        
        self._save_metadata()
        logger.info(f"Marked step {step_num} ({step.name}) as completed")
    
    def mark_step_skipped(self, step_num: int) -> None:
        """Mark a step as skipped.
        
        Args:
            step_num: Step number
        """
        if step_num not in self.steps:
            raise ValueError(f"Step {step_num} not found")
        
        step = self.steps[step_num]
        step.status = "skipped"
        step.completed_at = datetime.now().isoformat()
        
        # Mark downstream steps for rerun
        self._mark_downstream_for_rerun(step_num)
        
        self._save_metadata()
        logger.info(f"Marked step {step_num} ({step.name}) as skipped")
    
    def mark_step_failed(self, step_num: int, error: str) -> None:
        """Mark a step as failed.
        
        Args:
            step_num: Step number
            error: Error message
        """
        if step_num not in self.steps:
            raise ValueError(f"Step {step_num} not found")
        
        step = self.steps[step_num]
        step.status = "failed"
        step.error_message = error
        
        self._save_metadata()
        logger.error(f"Marked step {step_num} ({step.name}) as failed: {error}")
    
    def _mark_downstream_for_rerun(self, step_num: int) -> None:
        """Mark all downstream steps for rerun after step change.
        
        Args:
            step_num: Step number that changed
        """
        # Find all steps that depend on this step
        for other_step_num, other_step in self.steps.items():
            if step_num in other_step.dependencies and other_step.status == "completed":
                other_step.status = "pending"
                other_step.error_message = f"Pending rerun due to upstream change in step {step_num}"
                logger.debug(f"Marked step {other_step_num} for rerun due to change in step {step_num}")
        
        self._save_metadata()
    
    def get_next_runnable_step(self) -> Optional[int]:
        """Get the next step that can be run.
        
        Returns:
            Step number, or None if all completed
        """
        for step_num in range(10):
            step = self.steps[step_num]
            if step.status == "pending" and self._can_run_step(step_num):
                return step_num
        
        return None
    
    def reset_step(self, step_num: int, delete_outputs: bool = False) -> None:
        """Reset a step to pending state.
        
        Args:
            step_num: Step number
            delete_outputs: Whether to delete step outputs
        """
        if step_num not in self.steps:
            raise ValueError(f"Step {step_num} not found")
        
        step = self.steps[step_num]
        step.status = "pending"
        step.completed_at = None
        step.output_hash = None
        step.error_message = None
        
        # Mark downstream for rerun
        self._mark_downstream_for_rerun(step_num)
        
        self._save_metadata()
        logger.info(f"Reset step {step_num} ({step.name})")
    
    def get_step_summary(self) -> Dict[str, Any]:
        """Get summary of all steps.
        
        Returns:
            Summary with counts and overall status
        """
        completed = sum(1 for s in self.steps.values() if s.status == "completed")
        skipped = sum(1 for s in self.steps.values() if s.status == "skipped")
        failed = sum(1 for s in self.steps.values() if s.status == "failed")
        pending = sum(1 for s in self.steps.values() if s.status == "pending")
        
        return {
            "total": len(self.steps),
            "completed": completed,
            "skipped": skipped,
            "failed": failed,
            "pending": pending,
            "progress": f"{completed + skipped}/{len(self.steps)}",
            "overall_status": "complete" if pending == 0 and failed == 0 else (
                "has_failures" if failed > 0 else "in_progress"
            )
        }
