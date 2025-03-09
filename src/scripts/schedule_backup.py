#!/usr/bin/env python3
# src/scripts/schedule_backup.py
import os
import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Try both import styles to handle running from different directories
try:
    from src.utils.backup import S3Backup
    from src.config.settings import BASE_DIR
except ModuleNotFoundError:
    from utils.backup import S3Backup
    from config.settings import BASE_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{project_root}/backup_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Backup directories to AWS S3')
    parser.add_argument('--aws-key', help='AWS Access Key ID')
    parser.add_argument('--aws-secret', help='AWS Secret Access Key')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    parser.add_argument('--bucket', default='lzt-backup', help='S3 bucket name')
    parser.add_argument('--directory', default=str(BASE_DIR), help='Directory to backup')
    
    args = parser.parse_args()
    
    # Set AWS credentials
    if args.aws_key:
        os.environ['AWS_ACCESS_KEY_ID'] = args.aws_key
    if args.aws_secret:
        os.environ['AWS_SECRET_ACCESS_KEY'] = args.aws_secret
    
    # Check if credentials are set
    if not os.environ.get('AWS_ACCESS_KEY_ID') or not os.environ.get('AWS_SECRET_ACCESS_KEY'):
        logger.error("AWS credentials not set. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or use --aws-key and --aws-secret arguments.")
        logger.error("Make sure to use ACTUAL AWS credentials, not the placeholder values.")
        return 1
    
    logger.info(f"Starting backup of {args.directory} to S3 bucket {args.bucket}")
    
    # Initialize S3 backup
    s3_backup = S3Backup(aws_region=args.region, bucket_name=args.bucket)
    
    # Backup the directory
    success = s3_backup.backup_directory(Path(args.directory))
    
    if success:
        logger.info("Backup completed successfully")
        return 0
    else:
        logger.error("Backup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
