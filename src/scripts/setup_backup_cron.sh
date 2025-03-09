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
    # Prompt for AWS credentials
    read -p "Enter your AWS Access Key ID: " AWS_KEY
    read -p "Enter your AWS Secret Access Key: " AWS_SECRET
    
    # Add the daily backup job at 2 AM with the provided credentials
    echo "0 2 * * * cd $PROJECT_ROOT && $SCRIPT_PATH --aws-key '$AWS_KEY' --aws-secret '$AWS_SECRET' --bucket 'lzt-backup-personal' >> $PROJECT_ROOT/cron_backup.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    echo "Backup cron job installed. It will run daily at 2 AM."
else
    echo "Backup cron job already exists in crontab."
fi

# Clean up
rm "$TEMP_CRON"

echo "IMPORTANT: Your AWS credentials are now stored in your crontab."
echo "To view or edit the crontab: crontab -e"
echo "To test the backup now, run:"
echo "python -m src.scripts.schedule_backup --aws-key 'YOUR_ACTUAL_AWS_KEY' --aws-secret 'YOUR_ACTUAL_AWS_SECRET' --bucket 'lzt-backup-personal'"
