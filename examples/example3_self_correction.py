# Example 3: Self-Correction & Learning

**Scenario:** Agent makes an error, logs it, and learns.

```python
#!/usr/bin/env python3
"""
Example 3: Self-Correction & Learning
──────────────────────────────────────────────────────────
Demonstrates: Error logging, pattern detection, behavior update
"""

from pathlib import Path
import json
from datetime import datetime


class LearningSystem:
    """Simple learning system for demonstration."""
    
    def __init__(self, learnings_dir=".learnings"):
        self.learnings_dir = Path(learnings_dir)
        self.learnings_dir.mkdir(exist_ok=True)
        
        self.errors_file = self.learnings_dir / "ERRORS.md"
        self.learnings_file = self.learnings_dir / "LEARNINGS.md"
    
    def log_error(self, error_type, description, expected, root_cause, prevention):
        """Log error to ERRORS.md"""
        
        entry = f"""
## ERROR — {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Type:** {error_type}

**Description:** {description}

**Expected:** {expected}

**Root Cause:** {root_cause}

**Prevention:** {prevention}

---
"""
        
        with open(self.errors_file, "a") as f:
            f.write(entry)
        
        print(f"✓ Error logged: {error_type}")
        
        # Check for patterns
        self.check_patterns()
    
    def check_patterns(self, threshold=3):
        """Check if any error pattern repeats threshold times."""
        
        if not self.errors_file.exists():
            return
        
        content = self.errors_file.read_text()
        
        # Simple pattern: count "Type:" occurrences
        type_counts = {}
        for line in content.split("\n"):
            if line.startswith("**Type:**"):
                error_type = line.replace("**Type:**", "").strip()
                type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        # Find recurring patterns
        for error_type, count in type_counts.items():
            if count >= threshold:
                self.promote_to_learning(error_type, count)
    
    def promote_to_learning(self, error_type, count):
        """Promote recurring error to learning rule."""
        
        entry = f"""
## PROMOTED RULE — {datetime.now().strftime('%Y-%m-%d')}

**Pattern:** {error_type} (occurred {count} times)

**Rule:** [Auto-generated rule to prevent recurrence]

**Trigger:** Tasks involving {error_type.lower()}

**Action:** [Specific preventive action]

---
"""
        
        with open(self.learnings_file, "a") as f:
            f.write(entry)
        
        print(f"⚠ Pattern detected! '{error_type}' promoted to rule (occurred {count} times)")


def main():
    print("=" * 60)
    print("EXAMPLE 3: Self-Correction & Learning")
    print("=" * 60)
    
    learning_system = LearningSystem()
    
    # Simulate errors
    print("\nSimulating errors...\n")
    
    # Error 1: Wrong tax rate
    learning_system.log_error(
        error_type="Tax Rate Error",
        description="Used 20% VAT instead of 18% for Turkey",
        expected="Tax = revenue * 0.18",
        root_cause="Used default rate without checking country context",
        prevention="Add Turkey VAT (18%) to constants, check USER.md"
    )
    
    # Error 2: Same tax rate error (repeat)
    learning_system.log_error(
        error_type="Tax Rate Error",
        description="Again used 20% VAT instead of 18%",
        expected="Tax = revenue * 0.18",
        root_cause="Didn't check learned rules before calculation",
        prevention="Load promoted rules before financial tasks"
    )
    
    # Error 3: Tax rate again (triggers promotion)
    learning_system.log_error(
        error_type="Tax Rate Error",
        description="Third time: 20% instead of 18%",
        expected="Tax = revenue * 0.18",
        root_cause="System not checking learning database",
        prevention="Mandatory pre-task learning check"
    )
    
    # Different error type
    learning_system.log_error(
        error_type="File Format Skip",
        description="Skipped docx files, only read PDF",
        expected="Read all formats: docx, xlsx, PDF, notes",
        root_cause="Default preference for PDF",
        prevention="Add format priority checklist"
    )
    
    # Show generated files
    print("\n" + "=" * 60)
    print("GENERATED FILES")
    print("=" * 60)
    
    if learning_system.errors_file.exists():
        print(f"\n📄 {learning_system.errors_file}")
        print(learning_system.errors_file.read_text()[:500] + "...")
    
    if learning_system.learnings_file.exists():
        print(f"\n📄 {learning_system.learnings_file}")
        print(learning_system.learnings_file.read_text())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Self-correction workflow:
1. Error occurs → Log to ERRORS.md
2. Pattern detection → Count occurrences
3. If count ≥ 3 → Promote to LEARNINGS.md
4. Update behavior → Prevent future occurrence

This example showed:
- 3 tax rate errors → Promoted to rule
- 1 file format skip → Monitoring started
""")


if __name__ == "__main__":
    main()
