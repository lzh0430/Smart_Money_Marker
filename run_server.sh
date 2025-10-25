#!/bin/bash

# Smart Money Server Runner Script
# This script activates the virtual environment, cleans old logs, and runs the FastAPI server

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Smart Money Server..."
echo "Working directory: $SCRIPT_DIR"

# Function to cleanup old log files (older than 48 hours)
cleanup_old_logs() {
    echo "Cleaning up log files older than 48 hours..."
    
    # Find and remove server log files older than 48 hours
    find "$SCRIPT_DIR" -name "server.log" -type f -mtime +2 -delete 2>/dev/null || true
    
    echo "Log cleanup completed"
}
# Function to activate virtual environment and run server
run_server() {
    echo "Activating virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "myenv" ]; then
        echo "Error: Virtual environment 'myenv' not found!"
        echo "Please create the virtual environment first."
        exit 1
    fi
    
    # Activate virtual environment
    source myenv/bin/activate
        
    # Run the server
    echo "Starting Smart Money Server..."
    echo "Server will be available at: http://localhost:8443"
    echo "API documentation: http://localhost:8443/docs"
    echo "Press Ctrl+C to stop the server"
    echo "----------------------------------------"
    
    python3 server.py
    
    # Capture exit code
    SERVER_EXIT_CODE=$?
    
    # Deactivate virtual environment
    deactivate
    
    if [ $SERVER_EXIT_CODE -eq 0 ]; then
        echo "Server stopped successfully!"
    else
        echo "Server stopped with errors (exit code: $SERVER_EXIT_CODE)"
        exit $SERVER_EXIT_CODE
    fi
}

# Function to show server info
show_server_info() {
    echo "=========================================="
    echo "Smart Money Server Information"
    echo "=========================================="
    echo "Server: FastAPI HTTPS Server"
    echo "Purpose: REST API for SOL wallet data"
    echo "Default URL: http://localhost:8443"
    echo "API Docs: http://localhost:8443/docs"
    echo "Health Check: http://localhost:8443/health"
    echo "Endpoints:"
    echo "  - GET /health - Health check"
    echo "  - GET /wallets - Get wallets with filters"
    echo "  - GET /wallets/stats - Get collection statistics"
    echo "  - GET /wallets/{address} - Get specific wallet"
    echo "=========================================="
}

# Main execution
main() {
    echo "=========================================="
    echo "Smart Money Server Runner"
    echo "=========================================="
    
    # Show server information
    show_server_info
    
    # Step 1: Cleanup old logs
    cleanup_old_logs

    # Step 2: Run server
    run_server
    
    echo "=========================================="
    echo "Script completed!"
    echo "=========================================="
}

# Run main function
main "$@"
