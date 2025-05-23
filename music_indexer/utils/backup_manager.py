"""
Database backup and restore manager for the music indexer application.
"""
import os
import zipfile
import tarfile
import gzip
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger()


class BackupManager:
    """Manages backup and restore operations for the music indexer database and configuration."""
    
    def __init__(self, config_manager):
        """
        Initialize the backup manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.cache_file = config_manager.get("indexing", "cache_file", "cache/music_cache.db")
        self.config_file = "config.ini"
        
        logger.info("Backup manager initialized")
    
    def get_backup_info(self):
        """
        Get information about what will be backed up.
        
        Returns:
            dict: Backup information including file sizes and paths
        """
        info = {
            'database_file': self.cache_file,
            'config_file': self.config_file,
            'database_exists': os.path.exists(self.cache_file),
            'config_exists': os.path.exists(self.config_file),
            'database_size': 0,
            'config_size': 0,
            'total_files': 0
        }
        
        # Get database info
        if info['database_exists']:
            info['database_size'] = os.path.getsize(self.cache_file)
            
            # Get record count from database
            try:
                conn = sqlite3.connect(self.cache_file)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM files')
                info['total_files'] = cursor.fetchone()[0]
                conn.close()
            except Exception as e:
                logger.warning(f"Could not get database stats: {str(e)}")
        
        # Get config info
        if info['config_exists']:
            info['config_size'] = os.path.getsize(self.config_file)
        
        return info
    
    def create_backup(self, backup_path, format_type='zip', include_config=True, compression_level=6):
        """
        Create a backup of the database and optionally configuration.
        
        Args:
            backup_path (str): Path where backup should be created
            format_type (str): Archive format ('zip', '7z', 'tar', 'tar.gz')
            include_config (bool): Whether to include configuration file
            compression_level (int): Compression level (1-9, higher = more compression)
        
        Returns:
            tuple: (success, message, backup_file_path)
        """
        try:
            # Ensure backup directory exists
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Check if database exists
            if not os.path.exists(self.cache_file):
                return False, "Database file not found. Nothing to backup.", None
            
            # Create timestamp for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine backup filename
            base_name = os.path.splitext(os.path.basename(backup_path))[0]
            if not base_name:
                base_name = f"music_indexer_backup_{timestamp}"
            
            # Add extension based on format
            if format_type == 'zip':
                backup_file = os.path.join(backup_dir, f"{base_name}.zip")
                success, message = self._create_zip_backup(backup_file, include_config, compression_level)
            elif format_type == '7z':
                backup_file = os.path.join(backup_dir, f"{base_name}.7z")
                success, message = self._create_7z_backup(backup_file, include_config, compression_level)
            elif format_type == 'tar':
                backup_file = os.path.join(backup_dir, f"{base_name}.tar")
                success, message = self._create_tar_backup(backup_file, include_config, False)
            elif format_type == 'tar.gz':
                backup_file = os.path.join(backup_dir, f"{base_name}.tar.gz")
                success, message = self._create_tar_backup(backup_file, include_config, True)
            else:
                return False, f"Unsupported backup format: {format_type}", None
            
            if success:
                # Add metadata file to backup
                self._add_backup_metadata(backup_file, format_type, include_config)
                
                backup_size = os.path.getsize(backup_file)
                logger.info(f"Backup created successfully: {backup_file} ({backup_size} bytes)")
                return True, f"Backup created successfully: {backup_file}", backup_file
            else:
                return False, message, None
                
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False, f"Error creating backup: {str(e)}", None
    
    def _create_zip_backup(self, backup_file, include_config, compression_level):
        """Create a ZIP backup."""
        try:
            # Map compression level to zipfile constants
            compression_map = {
                1: zipfile.ZIP_STORED,  # No compression
                6: zipfile.ZIP_DEFLATED,  # Default
                9: zipfile.ZIP_DEFLATED   # Best compression
            }
            compression = compression_map.get(compression_level, zipfile.ZIP_DEFLATED)
            
            with zipfile.ZipFile(backup_file, 'w', compression) as zf:
                # Add database
                zf.write(self.cache_file, os.path.basename(self.cache_file))
                
                # Add config if requested and exists
                if include_config and os.path.exists(self.config_file):
                    zf.write(self.config_file, os.path.basename(self.config_file))
            
            return True, "ZIP backup created successfully"
            
        except Exception as e:
            return False, f"Error creating ZIP backup: {str(e)}"
    
    def _create_7z_backup(self, backup_file, include_config, compression_level):
        """Create a 7z backup using py7zr if available, otherwise fall back to ZIP."""
        try:
            import py7zr
            
            with py7zr.SevenZipFile(backup_file, 'w') as zf:
                # Add database
                zf.write(self.cache_file, os.path.basename(self.cache_file))
                
                # Add config if requested and exists
                if include_config and os.path.exists(self.config_file):
                    zf.write(self.config_file, os.path.basename(self.config_file))
            
            return True, "7z backup created successfully"
            
        except ImportError:
            # Fall back to ZIP if py7zr not available
            logger.warning("py7zr not available, falling back to ZIP format")
            backup_file_zip = backup_file.replace('.7z', '.zip')
            return self._create_zip_backup(backup_file_zip, include_config, compression_level)
        except Exception as e:
            return False, f"Error creating 7z backup: {str(e)}"
    
    def _create_tar_backup(self, backup_file, include_config, use_gzip):
        """Create a TAR backup, optionally with gzip compression."""
        try:
            mode = 'w:gz' if use_gzip else 'w'
            
            with tarfile.open(backup_file, mode) as tf:
                # Add database
                tf.add(self.cache_file, arcname=os.path.basename(self.cache_file))
                
                # Add config if requested and exists
                if include_config and os.path.exists(self.config_file):
                    tf.add(self.config_file, arcname=os.path.basename(self.config_file))
            
            format_name = "TAR.GZ" if use_gzip else "TAR"
            return True, f"{format_name} backup created successfully"
            
        except Exception as e:
            return False, f"Error creating TAR backup: {str(e)}"
    
    def _add_backup_metadata(self, backup_file, format_type, include_config):
        """Add metadata about the backup."""
        try:
            metadata = {
                'created_at': datetime.now().isoformat(),
                'format': format_type,
                'includes_config': include_config,
                'original_database_path': self.cache_file,
                'original_config_path': self.config_file if include_config else None,
                'backup_info': self.get_backup_info()
            }
            
            # Create temporary metadata file
            metadata_file = backup_file + '.metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Add to existing archive
            if format_type == 'zip':
                with zipfile.ZipFile(backup_file, 'a') as zf:
                    zf.write(metadata_file, 'backup_metadata.json')
            elif format_type in ['tar', 'tar.gz']:
                mode = 'a:gz' if format_type == 'tar.gz' else 'a'
                with tarfile.open(backup_file, mode) as tf:
                    tf.add(metadata_file, arcname='backup_metadata.json')
            
            # Clean up temporary file
            os.remove(metadata_file)
            
        except Exception as e:
            logger.warning(f"Could not add backup metadata: {str(e)}")
    
    def restore_backup(self, backup_file, restore_config=True, backup_existing=True):
        """
        Restore database and configuration from backup.
        
        Args:
            backup_file (str): Path to backup file
            restore_config (bool): Whether to restore configuration
            backup_existing (bool): Whether to backup existing files before restore
        
        Returns:
            tuple: (success, message)
        """
        try:
            if not os.path.exists(backup_file):
                return False, f"Backup file not found: {backup_file}"
            
            # Backup existing files if requested
            if backup_existing:
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if os.path.exists(self.cache_file):
                    backup_db = f"{self.cache_file}.backup_{backup_timestamp}"
                    shutil.copy2(self.cache_file, backup_db)
                    logger.info(f"Backed up existing database to: {backup_db}")
                
                if restore_config and os.path.exists(self.config_file):
                    backup_config = f"{self.config_file}.backup_{backup_timestamp}"
                    shutil.copy2(self.config_file, backup_config)
                    logger.info(f"Backed up existing config to: {backup_config}")
            
            # Determine archive format
            if backup_file.endswith('.zip'):
                success, message = self._restore_zip_backup(backup_file, restore_config)
            elif backup_file.endswith('.7z'):
                success, message = self._restore_7z_backup(backup_file, restore_config)
            elif backup_file.endswith('.tar.gz'):
                success, message = self._restore_tar_backup(backup_file, restore_config, True)
            elif backup_file.endswith('.tar'):
                success, message = self._restore_tar_backup(backup_file, restore_config, False)
            else:
                return False, "Unsupported backup format"
            
            if success:
                logger.info(f"Backup restored successfully from: {backup_file}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return False, f"Error restoring backup: {str(e)}"
    
    def _restore_zip_backup(self, backup_file, restore_config):
        """Restore from ZIP backup."""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zf:
                file_list = zf.namelist()
                
                # Restore database
                db_filename = os.path.basename(self.cache_file)
                if db_filename in file_list:
                    # Ensure cache directory exists
                    cache_dir = os.path.dirname(self.cache_file)
                    if cache_dir and not os.path.exists(cache_dir):
                        os.makedirs(cache_dir)
                    
                    zf.extract(db_filename, os.path.dirname(self.cache_file) or '.')
                    # Move to correct location if needed
                    extracted_path = os.path.join(os.path.dirname(self.cache_file) or '.', db_filename)
                    if extracted_path != self.cache_file:
                        shutil.move(extracted_path, self.cache_file)
                else:
                    return False, "Database file not found in backup"
                
                # Restore config if requested
                if restore_config:
                    config_filename = os.path.basename(self.config_file)
                    if config_filename in file_list:
                        zf.extract(config_filename, '.')
                        # Move to correct location if needed
                        if config_filename != self.config_file:
                            shutil.move(config_filename, self.config_file)
            
            return True, "ZIP backup restored successfully"
            
        except Exception as e:
            return False, f"Error restoring ZIP backup: {str(e)}"
    
    def _restore_7z_backup(self, backup_file, restore_config):
        """Restore from 7z backup."""
        try:
            import py7zr
            
            with py7zr.SevenZipFile(backup_file, 'r') as zf:
                # Extract to temporary directory
                temp_dir = f"{backup_file}_temp_extract"
                zf.extractall(temp_dir)
                
                # Move files to correct locations
                db_filename = os.path.basename(self.cache_file)
                temp_db_path = os.path.join(temp_dir, db_filename)
                
                if os.path.exists(temp_db_path):
                    # Ensure cache directory exists
                    cache_dir = os.path.dirname(self.cache_file)
                    if cache_dir and not os.path.exists(cache_dir):
                        os.makedirs(cache_dir)
                    
                    shutil.move(temp_db_path, self.cache_file)
                else:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return False, "Database file not found in backup"
                
                # Restore config if requested
                if restore_config:
                    config_filename = os.path.basename(self.config_file)
                    temp_config_path = os.path.join(temp_dir, config_filename)
                    if os.path.exists(temp_config_path):
                        shutil.move(temp_config_path, self.config_file)
                
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            return True, "7z backup restored successfully"
            
        except ImportError:
            return False, "py7zr library not available for 7z restore"
        except Exception as e:
            return False, f"Error restoring 7z backup: {str(e)}"
    
    def _restore_tar_backup(self, backup_file, restore_config, is_gzipped):
        """Restore from TAR backup."""
        try:
            mode = 'r:gz' if is_gzipped else 'r'
            
            with tarfile.open(backup_file, mode) as tf:
                # Extract to temporary directory
                temp_dir = f"{backup_file}_temp_extract"
                tf.extractall(temp_dir)
                
                # Move files to correct locations
                db_filename = os.path.basename(self.cache_file)
                temp_db_path = os.path.join(temp_dir, db_filename)
                
                if os.path.exists(temp_db_path):
                    # Ensure cache directory exists
                    cache_dir = os.path.dirname(self.cache_file)
                    if cache_dir and not os.path.exists(cache_dir):
                        os.makedirs(cache_dir)
                    
                    shutil.move(temp_db_path, self.cache_file)
                else:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return False, "Database file not found in backup"
                
                # Restore config if requested
                if restore_config:
                    config_filename = os.path.basename(self.config_file)
                    temp_config_path = os.path.join(temp_dir, config_filename)
                    if os.path.exists(temp_config_path):
                        shutil.move(temp_config_path, self.config_file)
                
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            format_name = "TAR.GZ" if is_gzipped else "TAR"
            return True, f"{format_name} backup restored successfully"
            
        except Exception as e:
            return False, f"Error restoring TAR backup: {str(e)}"
    
    def list_backup_contents(self, backup_file):
        """
        List contents of a backup file.
        
        Args:
            backup_file (str): Path to backup file
        
        Returns:
            tuple: (success, contents_list, metadata)
        """
        try:
            if not os.path.exists(backup_file):
                return False, [], None
            
            contents = []
            metadata = None
            
            if backup_file.endswith('.zip'):
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    for info in zf.infolist():
                        contents.append({
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'modified': datetime(*info.date_time)
                        })
                    
                    # Try to read metadata
                    if 'backup_metadata.json' in zf.namelist():
                        metadata = json.loads(zf.read('backup_metadata.json').decode())
            
            elif backup_file.endswith('.tar') or backup_file.endswith('.tar.gz'):
                mode = 'r:gz' if backup_file.endswith('.tar.gz') else 'r'
                with tarfile.open(backup_file, mode) as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            contents.append({
                                'name': member.name,
                                'size': member.size,
                                'modified': datetime.fromtimestamp(member.mtime)
                            })
                    
                    # Try to read metadata
                    try:
                        metadata_member = tf.getmember('backup_metadata.json')
                        metadata_file = tf.extractfile(metadata_member)
                        metadata = json.loads(metadata_file.read().decode())
                    except KeyError:
                        pass  # No metadata file
            
            return True, contents, metadata
            
        except Exception as e:
            logger.error(f"Error listing backup contents: {str(e)}")
            return False, [], None
    
    def verify_backup(self, backup_file):
        """
        Verify backup integrity.
        
        Args:
            backup_file (str): Path to backup file
        
        Returns:
            tuple: (success, verification_message)
        """
        try:
            if not os.path.exists(backup_file):
                return False, "Backup file not found"
            
            success, contents, metadata = self.list_backup_contents(backup_file)
            
            if not success:
                return False, "Could not read backup file"
            
            # Check for required files
            db_filename = os.path.basename(self.cache_file)
            has_database = any(item['name'] == db_filename for item in contents)
            
            if not has_database:
                return False, "Database file missing from backup"
            
            # Verify file sizes are reasonable
            db_size = next((item['size'] for item in contents if item['name'] == db_filename), 0)
            
            if db_size == 0:
                return False, "Database file appears to be empty"
            
            verification_msg = f"Backup verified successfully. Contains {len(contents)} files, database size: {db_size} bytes"
            
            if metadata:
                created_at = metadata.get('created_at', 'Unknown')
                total_files = metadata.get('backup_info', {}).get('total_files', 'Unknown')
                verification_msg += f", created: {created_at}, original records: {total_files}"
            
            return True, verification_msg
            
        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            return False, f"Error verifying backup: {str(e)}"