#!/bin/bash
# src/scripts/setup_backup_cron.sh

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/src/scripts/schedule_backup.py"

# Make the backup script executable
chmod +x "$SCRIPT_PATH"

# Create a temporary file for the crontab
TEMP_CRON=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# New crontab" > "$TEMP_CRON"

# Check if the backup job is already in the crontab
if ! grep -q "$SCRIPT_PATH" "$TEMP_CRON"; then
    # Add the daily backup job at 2 AM
    echo "0 2 * * * cd $PROJECT_ROOT && $SCRIPT_PATH --aws-key YOUR_AWS_KEY --aws-secret YOUR_AWS_SECRET >> $PROJECT_ROOT/cron_backup.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    echo "Backup cron job installed. It will run daily at 2 AM."
else
    echo "Backup cron job already exists in crontab."
fi

# Clean up
rm "$TEMP_CRON"

echo "IMPORTANT: Edit the crontab manually to set your AWS credentials:"
echo "crontab -e"
echo "Replace YOUR_AWS_KEY and YOUR_AWS_SECRET with your actual AWS credentials."
