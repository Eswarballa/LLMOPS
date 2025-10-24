import os
import shutil
import zipfile
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    
    @staticmethod
    async def save_upload(file: UploadFile, username: str, model_name: str) -> Tuple[str, str]:
        """
        Save uploaded zip file and extract it
        Returns: (zip_path, extracted_path)
        """
        # Create user directory
        user_dir = os.path.join(settings.UPLOAD_DIR, username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save zip file
        zip_filename = f"{model_name}.zip"
        zip_path = os.path.join(user_dir, zip_filename)
        
        try:
            # Save the uploaded file
            with open(zip_path, "wb") as buffer:
                content = await file.read()
                if len(content) > settings.MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large")
                buffer.write(content)
            
            logger.info(f"Saved zip file: {zip_path}")
            
            # Extract zip file
            extract_path = os.path.join(settings.MODELS_DIR, username, model_name)
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            logger.info(f"Extracted to: {extract_path}")
            
            # Validate extracted contents
            if not StorageService.validate_model_structure(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid model structure. Must contain app.py and requirements.txt in the root or a subdirectory"
                )
            
            return zip_path, extract_path
            
        except zipfile.BadZipFile as e:
            logger.error(f"Bad zip file: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise HTTPException(status_code=400, detail="Invalid zip file")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving upload: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    def validate_model_structure(path: str) -> bool:
        """
        Validate that the extracted model has required files
        Must contain: app.py and requirements.txt (can be in subdirectory)
        """
        required_files = {"app.py", "requirements.txt"}
        found_files = set()
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(path):
            for file in files:
                if file in required_files:
                    found_files.add(file)
            
            # If we found all files, return True
            if found_files == required_files:
                logger.info(f"Valid model structure found in {root}")
                return True
        
        logger.warning(f"Invalid model structure. Found files: {found_files}, Required: {required_files}")
        return False
    
    @staticmethod
    def cleanup_model(username: str, model_name: str):
        """Delete model files"""
        try:
            # Remove zip
            zip_path = os.path.join(settings.UPLOAD_DIR, username, f"{model_name}.zip")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            # Remove extracted files
            extract_path = os.path.join(settings.MODELS_DIR, username, model_name)
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            
            logger.info(f"Cleaned up model: {model_name}")
        except Exception as e:
            logger.error(f"Error cleaning up model: {e}")