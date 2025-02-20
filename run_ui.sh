#!/bin/bash

# Function to detect environment
detect_env() {
    if [[ -n $SSH_CLIENT ]] || [[ -n $SSH_TTY ]]; then
        echo "ssh"
    elif [[ $(tty) =~ /dev/tty[0-9] ]]; then
        echo "console"
    else
        echo "desktop"
    fi
}

# Function to check if X server is running
check_x_server() {
    if command -v xset &> /dev/null && xset q &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Get environment
ENV=$(detect_env)
echo "Detected environment: $ENV"

# Handle different environments
case $ENV in
    "ssh")
        if [ -z "$DISPLAY" ]; then
            echo "No display set, using virtual framebuffer..."
            export DISPLAY=:99
            Xvfb :99 -screen 0 1024x768x16 &
            XVFB_PID=$!
            sleep 1
            python app_ui.py
            kill $XVFB_PID
        else
            echo "Display already set to $DISPLAY"
            python app_ui.py
        fi
        ;;
    "console")
        if check_x_server; then
            echo "X server detected, using existing display"
            python app_ui.py
        else
            echo "No X server, using virtual framebuffer..."
            export DISPLAY=:99
            Xvfb :99 -screen 0 1024x768x16 &
            XVFB_PID=$!
            sleep 1
            python app_ui.py
            kill $XVFB_PID
        fi
        ;;
    "desktop")
        echo "Running in desktop environment"
        python app_ui.py
        ;;
esac
