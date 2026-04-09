#!/bin/bash
# TP3 - Scanning Rate EDMD
# Helper script to build, run simulations, and generate plots

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
JAR="$PROJECT_DIR/simulation/target/tp3-scanning-rate-1.0-SNAPSHOT.jar"
PYTHON="$PROJECT_DIR/.venv/bin/python"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== TP3: Scanning Rate EDMD ===${NC}"

# Step 1: Build Java simulation
echo -e "${GREEN}[1/5] Building Java simulation...${NC}"
cd "$PROJECT_DIR/simulation"
mvn clean package -q
cd "$PROJECT_DIR"

# Step 2: Setup Python environment
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}[2/5] Creating virtual environment...${NC}"
    uv venv .venv
    uv pip install -r requirements.txt
else
    echo -e "${GREEN}[2/5] Virtual environment already exists${NC}"
fi

# Step 3: Run Exercise 1.1
echo -e "${GREEN}[3/5] Running Exercise 1.1 (Execution time vs N)...${NC}"
$PYTHON analysis/ex1_execution_time.py

# Step 4: Run Exercise 1.2 (also generates data for 1.3 and 1.4)
echo -e "${GREEN}[4/5] Running Exercise 1.2 (Scanning rate)...${NC}"
$PYTHON analysis/ex2_scanning_rate.py

# Step 5: Run Exercises 1.3 and 1.4
echo -e "${GREEN}[5/5] Running Exercises 1.3 and 1.4 (Fraction used & Radial profiles)...${NC}"
$PYTHON analysis/ex3_fraction_used.py
$PYTHON analysis/ex4_radial_profiles.py

echo -e "${BLUE}=== All exercises completed! ===${NC}"
echo "Output files are in: $PROJECT_DIR/output/"
