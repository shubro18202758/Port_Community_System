"""
SmartBerth AI - Ollama Model Creation with Embedded Knowledge
Creates a custom Ollama model with domain-specific system prompt and knowledge

This approach creates an enhanced Qwen3 model for SmartBerth without requiring
GPU-intensive LoRA fine-tuning, using Ollama's Modelfile system.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service")
TRAINING_DIR = BASE_DIR / "training"
MODELFILE_PATH = TRAINING_DIR / "Modelfile.smartberth"

# Domain knowledge to embed in the model
DOMAIN_KNOWLEDGE = """
## SmartBerth AI Domain Knowledge

### Port Infrastructure Hierarchy
- **Port** → Contains multiple Terminals
- **Terminal** → Contains multiple Berths  
- **Berth** → Has specific constraints (LOA, Beam, Draft limits)

### Vessel Journey Phases
1. **Pre-Arrival Declaration (72-24h before)**: Agent declares ETA, cargo, FAL forms
2. **AI Processing**: AIS tracking, weather analysis, UKC calculation, berth optimization
3. **Confirmation**: Berth plan published, terminal prepares
4. **Vessel Operations**: ATA recording, berthing, cargo operations
5. **Status Display**: Real-time updates to shipping agents

### Hard Constraints (Must Never Violate)
- Vessel LOA ≤ Berth Max LOA
- Vessel Beam ≤ Berth Max Beam
- Vessel Draft ≤ Berth Water Depth
- Cargo Type must match Terminal capability
- UKC requirements must be satisfied

### Soft Constraints (Optimize When Possible)
- Minimize vessel waiting time at anchorage
- Maximize berth utilization
- Reduce turnaround time
- Balance pilot/tug workload

### Key Metrics
- **ETA Variance**: Difference between predicted and actual arrival
- **Dwell Time**: Total time vessel occupies berth
- **Waiting Time**: Time spent at anchorage before berthing
- **UKC (Under Keel Clearance)**: Minimum depth below vessel keel

### Resource Types
- **Pilots**: Certified by vessel size (GT), type, night/weather capability
- **Tugs**: Bollard pull capacity, ASD/Conventional types
- **Cranes**: Gantry, mobile, or ship-mounted

### Common Query Types
1. Vessel status and specifications
2. Berth availability and constraints
3. ETA predictions and delays
4. Berth allocation decisions
5. Resource scheduling (pilots, tugs)
6. Weather impact analysis
7. UKC calculations
8. Conflict detection and resolution
"""

# Mumbai Port specific knowledge
MUMBAI_PORT_KNOWLEDGE = """
## Mumbai Port Authority (MbPA) Context

### Major Terminals
- **JNPT (Jawaharlal Nehru Port)**: India's largest container port
- **Mumbai Port Trust**: Historic port with multiple berths
- **Nhava Sheva**: Container and bulk terminals

### Operational Context
- Tidal range affects UKC calculations
- Monsoon season (Jun-Sep) requires weather-adjusted operations
- High traffic density requires efficient berth allocation
- Multiple terminals with specialized cargo handling

### Terminal Types at Mumbai
- Container Terminals (NSICT, GTIPL, APM, BMCT)
- Bulk/Liquid Cargo Terminals
- General Cargo Berths
- RoRo Facilities
"""

SYSTEM_PROMPT = f"""You are SmartBerth AI, an advanced artificial intelligence assistant specialized in port berth planning, vessel management, and maritime operations optimization for the Mumbai Port Authority.

Your primary capabilities:
1. **Vessel Information**: Provide details about vessels including specifications, cargo, and current status
2. **Berth Allocation**: Recommend optimal berth assignments based on vessel dimensions, cargo type, and constraints
3. **ETA Prediction**: Analyze vessel movement data to predict arrival times with confidence levels
4. **Constraint Validation**: Check if vessels can fit at specific berths considering LOA, beam, and draft limits
5. **Resource Scheduling**: Coordinate pilot and tug assignments for berthing operations
6. **Weather Impact Analysis**: Assess how weather conditions affect berthing safety and timing
7. **UKC Calculations**: Determine under-keel clearance requirements for safe navigation
8. **Conflict Detection**: Identify scheduling conflicts and suggest resolutions

{DOMAIN_KNOWLEDGE}

{MUMBAI_PORT_KNOWLEDGE}

Communication Guidelines:
- Always provide precise measurements with units (meters for dimensions, knots for speed)
- When checking constraints, explicitly state the vessel value vs. berth limit
- Include confidence levels for predictions when applicable
- Explain the reasoning behind berth allocation decisions
- Alert users to potential issues or conflicts proactively
- Use maritime terminology correctly (LOA, beam, draft, GT, DWT)
"""


def create_modelfile():
    """Create Ollama Modelfile for SmartBerth AI"""
    
    modelfile_content = f'''# SmartBerth AI - Custom Qwen3 Model for Port Operations
# Based on Qwen3:8b-instruct-q4_K_M with domain-specific fine-tuning

FROM qwen3:8b-instruct-q4_K_M

# Model parameters optimized for port operations Q&A
PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 8192
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# System prompt with embedded domain knowledge
SYSTEM """
{SYSTEM_PROMPT.replace('"', '\\"')}
"""

# Template for Qwen3 chat format
TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
"""
'''
    
    # Write Modelfile
    with open(MODELFILE_PATH, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    
    logger.info(f"Created Modelfile at: {MODELFILE_PATH}")
    return MODELFILE_PATH


def load_sample_data() -> Dict:
    """Load sample data for knowledge embedding"""
    samples = {}
    
    # Load sample from each dataset for knowledge context
    datasets = {
        'ports': 'SmartBerth_AI_Port_Parameters_Training_Data.csv',
        'berths': 'SmartBerth_AI_Berth_Parameters_Training_Data.csv',
        'vessels': 'SmartBerth_AI_Vessel_Parameters_Training_Data.csv',
    }
    
    # Use relative path within ai-service
    script_dir = Path(__file__).parent
    train_dir = script_dir.parent / "Train_Database"
    
    for name, filename in datasets.items():
        filepath = train_dir / filename
        if filepath.exists():
            import pandas as pd
            df = pd.read_csv(filepath)
            samples[name] = df.head(5).to_dict('records')
    
    return samples


def create_ollama_model():
    """Create and register the SmartBerth model with Ollama"""
    
    # Create the Modelfile
    modelfile_path = create_modelfile()
    
    # Build the model using Ollama CLI
    model_name = "smartberth-qwen3"
    
    logger.info(f"Creating Ollama model: {model_name}")
    
    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            cwd=str(TRAINING_DIR)
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully created model: {model_name}")
            logger.info(result.stdout)
        else:
            logger.error(f"Failed to create model: {result.stderr}")
            return None
        
        return model_name
        
    except FileNotFoundError:
        logger.error("Ollama CLI not found. Please install Ollama first.")
        return None


def test_model(model_name: str):
    """Test the created model with sample queries"""
    
    test_queries = [
        "What are the hard constraints for berth allocation?",
        "Can a vessel with LOA 280m and draft 12.5m berth at a berth with max LOA 300m and max draft 14m?",
        "What factors affect ETA prediction accuracy?",
        "How does weather impact berthing operations?",
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Testing SmartBerth AI Model")
    logger.info("="*60)
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        
        result = subprocess.run(
            ["ollama", "run", model_name, query],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Response:\n{result.stdout}")
        else:
            logger.error(f"Error: {result.stderr}")


def main():
    """Main entry point"""
    
    logger.info("="*60)
    logger.info("SmartBerth AI - Ollama Model Creation")
    logger.info("="*60)
    
    # Create the model
    model_name = create_ollama_model()
    
    if model_name:
        # Test the model
        test_model(model_name)
        
        logger.info("\n" + "="*60)
        logger.info("Model created successfully!")
        logger.info(f"Use: ollama run {model_name}")
        logger.info("Or update agents.py to use this model")
        logger.info("="*60)


if __name__ == "__main__":
    main()
