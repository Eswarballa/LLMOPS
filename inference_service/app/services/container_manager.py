import docker
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

class ContainerManager:
    """
    Manages Docker containers for ML models
    - Starts containers on demand
    - Stops idle containers
    - Tracks container status and ports
    """
    
    def __init__(self):
        try:
            self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            self.client.ping()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
        
        self.running_containers = {}  # container_id: {port, last_used, model_id}
    
    def start_container(self, container_id: str, model_id: int) -> Optional[int]:
        """
        Start a container and return its external port
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        try:
            # Check if already running
            if container_id in self.running_containers:
                logger.info(f"Container {container_id[:12]} already running")
                self.running_containers[container_id]['last_used'] = datetime.utcnow()
                return self.running_containers[container_id]['port']
            
            # Check if we're at capacity
            if len(self.running_containers) >= settings.MAX_RUNNING_CONTAINERS:
                logger.warning("Max containers reached, stopping oldest idle container")
                self._stop_oldest_idle_container()
            
            # Get container
            container = self.client.containers.get(container_id)
            
            # Start if not running
            if container.status != 'running':
                logger.info(f"Starting container {container_id[:12]}...")
                container.start()
                
                # Wait for container to be ready
                time.sleep(2)
                container.reload()
            
            # Get external port
            port_info = container.attrs['NetworkSettings']['Ports'].get('8080/tcp')
            if not port_info or len(port_info) == 0:
                raise Exception("No port mapping found")
            
            external_port = int(port_info[0]['HostPort'])
            
            # Track running container
            self.running_containers[container_id] = {
                'port': external_port,
                'last_used': datetime.utcnow(),
                'model_id': model_id,
                'container': container
            }
            
            logger.info(f"Container {container_id[:12]} running on port {external_port}")
            return external_port
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    def stop_container(self, container_id: str):
        """Stop a running container"""
        if not self.client:
            return
        
        try:
            if container_id in self.running_containers:
                container = self.running_containers[container_id]['container']
                container.stop()
                del self.running_containers[container_id]
                logger.info(f"Stopped container {container_id[:12]}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
    
    def get_container_port(self, container_id: str) -> Optional[int]:
        """Get external port for a running container"""
        if container_id in self.running_containers:
            self.running_containers[container_id]['last_used'] = datetime.utcnow()
            return self.running_containers[container_id]['port']
        return None
    
    def is_container_running(self, container_id: str) -> bool:
        """Check if container is running"""
        return container_id in self.running_containers
    
    def _stop_oldest_idle_container(self):
        """Stop the oldest idle container to free up resources"""
        if not self.running_containers:
            return
        
        # Find oldest idle container
        oldest = None
        oldest_time = datetime.utcnow()
        
        for cid, info in self.running_containers.items():
            if info['last_used'] < oldest_time:
                oldest_time = info['last_used']
                oldest = cid
        
        if oldest:
            logger.info(f"Stopping idle container {oldest[:12]}")
            self.stop_container(oldest)
    
    async def cleanup_idle_containers(self):
        """Background task to cleanup idle containers"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                cutoff_time = datetime.utcnow() - timedelta(seconds=settings.CONTAINER_IDLE_TIMEOUT)
                to_stop = []
                
                for cid, info in self.running_containers.items():
                    if info['last_used'] < cutoff_time:
                        to_stop.append(cid)
                
                for cid in to_stop:
                    logger.info(f"Stopping idle container {cid[:12]} (idle for {settings.CONTAINER_IDLE_TIMEOUT}s)")
                    self.stop_container(cid)
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def get_stats(self) -> dict:
        """Get container statistics"""
        return {
            'running_containers': len(self.running_containers),
            'max_containers': settings.MAX_RUNNING_CONTAINERS,
            'containers': [
                {
                    'container_id': cid[:12],
                    'model_id': info['model_id'],
                    'port': info['port'],
                    'last_used': info['last_used'].isoformat()
                }
                for cid, info in self.running_containers.items()
            ]
        }

# Global instance
container_manager = ContainerManager()