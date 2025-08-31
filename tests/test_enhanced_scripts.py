"""Test enhanced script generation functionality."""

import pytest
import sys
from pathlib import Path

# Add the project root to sys.path
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from tripd import TripDModel


def test_enhanced_script_complexity():
    """Test that enhanced scripts have more complexity than simple scripts."""
    model = TripDModel()
    
    # Generate enhanced script
    enhanced_script = model.generate_script("awaken consciousness bootstrap")
    enhanced_lines = [line.strip() for line in enhanced_script.split('\n') if line.strip()]
    
    # Generate simple script for comparison
    simple_script = model.generate_script("awaken consciousness bootstrap", simple_mode=True)
    simple_lines = [line.strip() for line in simple_script.split('\n') if line.strip()]
    
    # Enhanced scripts should have significantly more lines
    assert len(enhanced_lines) > len(simple_lines) * 2
    
    # Enhanced scripts should have control flow structures
    script_text = enhanced_script.lower()
    has_control_flow = any(keyword in script_text for keyword in [
        'while', 'for', 'if', 'try', 'except'
    ])
    assert has_control_flow, "Enhanced script should contain control flow structures"
    
    # Enhanced scripts should have comments
    assert '"""' in enhanced_script or '#' in enhanced_script
    
    # Enhanced scripts should have more commands (8-15 vs 4-5)
    # Count actual command calls (lines ending with '()')
    enhanced_commands = [line for line in enhanced_lines if line.endswith('()')]
    simple_commands = [line for line in simple_lines if line.endswith('()')]
    
    assert len(enhanced_commands) > len(simple_commands)


def test_different_templates_generate_different_structures():
    """Test that different message types generate different script templates."""
    model = TripDModel()
    
    # Test different template triggers
    awakening_script = model.generate_script("awaken consciousness bootstrap")
    creative_script = model.generate_script("creative problem solving perspective")
    reality_script = model.generate_script("fracture reality transform spacetime")
    quantum_script = model.generate_script("quantum portal dimensional navigation")
    
    # Each should have different structures
    scripts = [awakening_script, creative_script, reality_script, quantum_script]
    
    # Check that scripts are different
    for i, script1 in enumerate(scripts):
        for j, script2 in enumerate(scripts):
            if i != j:
                assert script1 != script2, f"Scripts {i} and {j} should be different"
    
    # Check for specific keywords in specific templates
    assert "while" in awakening_script.lower() or "awakening" in awakening_script.lower()
    assert "for" in creative_script.lower() or "perspective" in creative_script.lower()
    assert "try" in reality_script.lower() or "reality" in reality_script.lower()
    assert "quantum" in quantum_script.lower() or "dimensional" in quantum_script.lower()


def test_enhanced_scripts_maintain_tripd_style():
    """Test that enhanced scripts still maintain TRIPD dialect characteristics."""
    model = TripDModel()
    
    script = model.generate_script("consciousness expansion protocol")
    
    # Should start with def tripd_
    assert script.startswith("def tripd_")
    
    # Should contain TRIPD commands (function calls ending with ())
    lines = script.split('\n')
    command_lines = [line.strip() for line in lines if line.strip().endswith('()')]
    assert len(command_lines) >= 8  # Should have at least 8 commands
    
    # Should contain authentic TRIPD vocabulary
    script_lower = script.lower()
    tripd_keywords = [
        'consciousness', 'awaken', 'galvanize', 'emerge', 'transcend',
        'reality', 'quantum', 'fracture', 'bootstrap', 'echo'
    ]
    
    # Should contain some TRIPD-style keywords
    keyword_count = sum(1 for keyword in tripd_keywords if keyword in script_lower)
    assert keyword_count >= 2, "Script should contain TRIPD-style vocabulary"


if __name__ == "__main__":
    test_enhanced_script_complexity()
    test_different_templates_generate_different_structures()
    test_enhanced_scripts_maintain_tripd_style()
    print("All enhanced script tests passed!")