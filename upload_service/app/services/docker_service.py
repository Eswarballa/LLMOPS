import os
import docker
from docker.errors import BuildError, APIError
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        try:
            # Try to connect using the Docker socket
            self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            # Test the connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            logger.warning("Docker service will not be available. Ensure Docker socket is mounted.")
            self.client = None
    
    def create_dockerfile(self, model_path: str) -> str:
        """Create Dockerfile for the model"""
        dockerfile_content = """FROM python:3.10-slim

WORKDIR /app

# Copy model files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (internal container port)
# Docker will map this to a random external port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
"""
        dockerfile_path = os.path.join(model_path, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        logger.info(f"Created Dockerfile at {dockerfile_path}")
        return dockerfile_path
    
    def build_image(self, model_path: str, username: str, model_name: str) -> str:
        """
        Build Docker image from model
        Returns: image tag
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        # Create Dockerfile
        self.create_dockerfile(model_path)
        
        # Generate image tag
        image_tag = f"{settings.DOCKER_IMAGE_PREFIX}/{username}/{model_name}:latest".lower()
        
        try:
            logger.info(f"Building Docker image: {image_tag}")
            
            # Build image
            image, build_logs = self.client.images.build(
                path=model_path,
                tag=image_tag,
                rm=True,
                forcerm=True
            )
            
            # Log build output
            for log in build_logs:
                if 'stream' in log:
                    logger.info(log['stream'].strip())
            
            logger.info(f"Successfully built image: {image_tag}")
            return image_tag
            
        except BuildError as e:
            logger.error(f"Docker build failed: {e}")
            raise Exception(f"Failed to build Docker image: {str(e)}")
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise Exception(f"Docker API error: {str(e)}")
    
    def push_image(self, image_tag: str) -> bool:
        """Push image to registry (optional)"""
        if not self.client:
            return False
        
        try:
            logger.info(f"Pushing image to registry: {image_tag}")
            
            # Push to registry
            for line in self.client.images.push(image_tag, stream=True, decode=True):
                if 'status' in line:
                    logger.info(line['status'])
            
            logger.info(f"Successfully pushed image: {image_tag}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to push image (optional): {e}")
            return False
    
    def create_container(self, image_tag: str, container_name: str) -> dict:
        """
        Create a container from the image (don't start it yet)
        Returns: dict with container_id and port_mapping
        
        IMPORTANT: Each container's port 8080 is mapped to a RANDOM external port.
        This allows multiple models to run simultaneously without port conflicts.
        
        Example:
        - User1/Model1: Internal 8080 → External 32768
        - User1/Model2: Internal 8080 → External 32769
        - User2/Model1: Internal 8080 → External 32770
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        try:
            logger.info(f"Creating container: {container_name}")
            
            # Create container with port mapping
            # ports={'8080/tcp': None} means Docker will assign a random available port
            container = self.client.containers.create(
                image_tag,
                name=container_name,
                detach=True,
                ports={'8080/tcp': None}  # Random external port assignment
            )
            
            # Get the assigned port (will be available after starting)
            container_info = {
                'container_id': container.id,
                'container_name': container_name,
                'internal_port': 8080,
                'status': 'created'
            }
            
            logger.info(f"Created container: {container.id}")
            logger.info(f"Port 8080 will be mapped to a random external port when started")
            
            return container_info
            
        except APIError as e:
            logger.error(f"Failed to create container: {e}")
            raise Exception(f"Failed to create container: {str(e)}")
    
    def get_container_port(self, container_id: str) -> int:
        """
        Get the external port mapped to container's port 8080
        This is called by the inference service after starting the container
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        try:
            container = self.client.containers.get(container_id)
            # Get port mapping
            port_info = container.attrs['NetworkSettings']['Ports'].get('8080/tcp')
            if port_info and len(port_info) > 0:
                external_port = int(port_info[0]['HostPort'])
                logger.info(f"Container {container_id[:12]} port 8080 → Host port {external_port}")
                return external_port
            else:
                logger.warning(f"No port mapping found for container {container_id[:12]}")
                return None
        except Exception as e:
            logger.error(f"Failed to get container port: {e}")
            return None
    
    def start_container(self, container_id: str) -> int:
        """
        Start a container and return its external port
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container: {container_id[:12]}")
            
            # Get the assigned external port
            external_port = self.get_container_port(container_id)
            return external_port
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise Exception(f"Failed to start container: {str(e)}")
    
    def stop_container(self, container_id: str):
        """Stop a running container"""
        if not self.client:
            return
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Stopped container: {container_id[:12]}")
        except Exception as e:
            logger.warning(f"Failed to stop container: {e}")
    
    def remove_container(self, container_id: str):
        """Remove a container"""
        if not self.client:
            return
        
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f"Removed container: {container_id[:12]}")
        except Exception as e:
            logger.warning(f"Failed to remove container: {e}")
    
    def remove_image(self, image_tag: str):
        """Remove Docker image"""
        if not self.client:
            return
        
        try:
            self.client.images.remove(image_tag, force=True)
            logger.info(f"Removed image: {image_tag}")
        except Exception as e:
            logger.warning(f"Failed to remove image: {e}")

docker_service = DockerService()