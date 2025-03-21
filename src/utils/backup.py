import os
import logging
import boto3
from pathlib import Path
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3Backup:
    """
    Handles backing up directories to AWS S3
    """
    def __init__(self, aws_region='us-west-2', bucket_name='lzt-backup'):
        """
        Initialize the S3 backup utility
        
        Args:
            aws_region (str): AWS region to use
            bucket_name (str): S3 bucket name for backups
        """
        self.aws_region = aws_region
        self.bucket_name = bucket_name
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        
    def ensure_bucket_exists(self):
        """
        Ensure the backup bucket exists, create it if it doesn't
        
        Returns:
            bool: True if bucket exists or was created successfully
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            
            # If bucket doesn't exist, create it
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                    )
                    logger.info(f"Created bucket {self.bucket_name}")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            elif error_code == '403':
                logger.error(f"Access denied to bucket {self.bucket_name}. Please check your AWS credentials and permissions.")
                return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False
    
    def backup_directory(self, directory_path, max_files=100):
        """
        Backup a directory to S3
        
        Args:
            directory_path (Path): Path to directory to backup
            max_files (int): Maximum number of files to backup (for testing/safety)
            
        Returns:
            bool: True if backup was successful
        """
        if not self.ensure_bucket_exists():
            return False
            
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory {directory_path} does not exist or is not a directory")
            return False
            
        # Create a timestamp for the backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_prefix = f"{directory_path.name}_{timestamp}/"
        
        success = True
        file_count = 0
        
        try:
            # Walk through the directory and upload all files
            for root, _, files in os.walk(directory_path):
                for file in files:
                    # Skip hidden files and common system files
                    if file.startswith('.') or file in ['Thumbs.db', 'desktop.ini', '.DS_Store']:
                        continue
                        
                    # Limit the number of files for testing/safety
                    if file_count >= max_files:
                        logger.info(f"Reached maximum file limit ({max_files}). Stopping backup.")
                        break
                        
                    local_path = Path(root) / file
                    
                    # Skip files larger than 100MB for safety
                    if local_path.stat().st_size > 100 * 1024 * 1024:
                        logger.warning(f"Skipping large file {local_path} (> 100MB)")
                        continue
                    
                    # Create the S3 key (path in the bucket)
                    try:
                        relative_path = local_path.relative_to(directory_path.parent)
                        s3_key = f"{backup_prefix}/{relative_path}"
                        
                        logger.info(f"Uploading {local_path} to {s3_key}")
                        self.s3_client.upload_file(
                            str(local_path),
                            self.bucket_name,
                            s3_key
                        )
                        file_count += 1
                        
                        # Print progress every 10 files
                        if file_count % 10 == 0:
                            logger.info(f"Uploaded {file_count} files so far...")
                            
                    except ClientError as e:
                        logger.error(f"Failed to upload {local_path}: {e}")
                        success = False
                    except Exception as e:
                        logger.error(f"Error processing {local_path}: {str(e)}")
                        success = False
                
                # Break out of the outer loop too if we hit the file limit
                if file_count >= max_files:
                    break
            
            if success:
                logger.info(f"Successfully backed up {file_count} files from {directory_path} to S3")
            return success
            
        except KeyboardInterrupt:
            logger.warning("Backup interrupted by user after uploading {file_count} files")
            return False
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return False
