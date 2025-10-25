#!/bin/bash

# SOL Wallets Scraper Runner Script
# This script activates the virtual environment, cleans old logs, and runs the scraper

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting SOL Wallets Scraper..."
echo "Working directory: $SCRIPT_DIR"

# Function to cleanup old log files (older than 48 hours)
cleanup_old_logs() {
    echo "Cleaning up log files older than 48 hours..."
    
    # Find and remove log files older than 48 hours
    find "$SCRIPT_DIR" -name "sol_wallets_scraper.log" -type f -mtime +2 -delete 2>/dev/null || true
    
    echo "Log cleanup completed"
}

# Function to activate virtual environment and run scraper
run_scraper() {
    echo "Activating virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "myenv" ]; then
        echo "Error: Virtual environment 'myenv' not found!"
        echo "Please create the virtual environment first."
        exit 1
    fi
    
    # Activate virtual environment
    source myenv/bin/activate
    
    # Run the scraper
    echo "Running SOL wallets scraper..."
    python3 sol_wallets_scraper.py
    
    # Capture exit code
    SCRAPER_EXIT_CODE=$?
    
    # Deactivate virtual environment
    deactivate
    
    if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
        echo "Scraper completed successfully!"
    else
        echo "Scraper completed with errors (exit code: $SCRAPER_EXIT_CODE)"
        exit $SCRAPER_EXIT_CODE
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "SOL Wallets Scraper Runner"
    echo "=========================================="
    
    # Step 1: Cleanup old logs
    cleanup_old_logs
    
    # Step 2: Run scraper
    run_scraper
    
    echo "=========================================="
    echo "Script completed successfully!"
    echo "=========================================="
}

# Run main function
main "$@"
