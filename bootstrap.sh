#!/bin/bash
# ========================
# LLMOPS BOOTSTRAP SCRIPT
# ========================
# This script creates VMs on OpenStack and sets up base dependencies.
# Application code and Docker images will be deployed by bootstrap-runner.sh

# ========================
# CONFIGURATION VARIABLES
# ========================
IMAGE="ubuntu_24"            # Base image
KEY_NAME="eswar-key"         # Your uploaded key
SEC_GROUP="SSH-AOS"          # Security group
INTERNAL_NET="llmops-net"    # Internal network
SUBNET="llmops-subnet"
ROUTER="llmops-router"
SUBNET_CIDR="10.0.0.0/24"    # Internal subnet range
PUBLIC_NET="public1"         # External network

# VM Names
VM_AUTH="vm-core-auth"
VM_UPLOAD="vm-upload-kafka"
VM_INFER="vm-inference-ctrl"
VM_LB="vm-lb-gateway"

# Flavor mapping
FLAVOR_SMALL="m1.small"
FLAVOR_MEDIUM="m1.medium"

# ========================
# CREATE NETWORK & ROUTER
# ========================
echo "Creating internal network and subnet..."
openstack network create $INTERNAL_NET
openstack subnet create --network $INTERNAL_NET \
  --subnet-range $SUBNET_CIDR \
  --gateway 10.0.0.1 $SUBNET

echo "Creating router and connecting to external network..."
openstack router create $ROUTER
openstack router set --external-gateway $PUBLIC_NET $ROUTER
openstack router add subnet $ROUTER $SUBNET
echo "✅ Network setup complete!"

# ========================
# CREATE VMs
# ========================
echo "Creating 4 VMs for LLMOPS..."
openstack server create \
  --image $IMAGE --flavor $FLAVOR_SMALL \
  --key-name $KEY_NAME --network $INTERNAL_NET \
  --security-group $SEC_GROUP \
  --user-data cloud-init-auth.yml \
  $VM_AUTH

openstack server create \
  --image $IMAGE --flavor $FLAVOR_SMALL \
  --key-name $KEY_NAME --network $INTERNAL_NET \
  --security-group $SEC_GROUP \
  --user-data cloud-init-upload.yml \
  $VM_UPLOAD

openstack server create \
  --image $IMAGE --flavor $FLAVOR_MEDIUM \
  --key-name $KEY_NAME --network $INTERNAL_NET \
  --security-group $SEC_GROUP \
  --user-data cloud-init-infer.yml \
  $VM_INFER

openstack server create \
  --image $IMAGE --flavor $FLAVOR_SMALL \
  --key-name $KEY_NAME --network $INTERNAL_NET \
  --security-group $SEC_GROUP \
  --user-data cloud-init-lb.yml \
  $VM_LB

echo "✅ All VMs launched!"

# ========================
# ASSIGN FLOATING IPs
# ========================
echo "Assigning floating IPs..."
for VM in $VM_AUTH $VM_UPLOAD $VM_INFER $VM_LB; do
    FLOAT_IP=$(openstack floating ip create $PUBLIC_NET -f value -c floating_ip_address)
    openstack server add floating ip $VM $FLOAT_IP
    echo "$VM -> $FLOAT_IP"
done

# ========================
# POST-BOOT: BOOTSTRAP-RUNNER SETUP
# ========================
# Place a minimal bootstrap-runner.sh on each VM to run after VM is ready
setup_runner() {
    VM_IP=$1
    ROLE=$2
    echo "Setting up bootstrap-runner on $ROLE ($VM_IP)..."

    ssh -o StrictHostKeyChecking=no ubuntu@$VM_IP <<EOF
mkdir -p /srv/llmops
cat <<RUNNER > /srv/llmops/bootstrap-runner.sh
#!/bin/bash
# Post-boot bootstrap: fetch code, deploy Docker containers
cd /srv/llmops
if [ ! -d app ]; then
    git clone https://github.com/your-org/llmops.git app
fi
cd app
# Build or pull Docker images
docker-compose pull
docker-compose up -d
# Optional: register health checks, services
RUNNER
chmod +x /srv/llmops/bootstrap-runner.sh
EOF
}

# Map roles to VMs
setup_runner $(openstack server show $VM_AUTH -f value -c addresses | cut -d'=' -f2) auth
setup_runner $(openstack server show $VM_UPLOAD -f value -c addresses | cut -d'=' -f2) upload
setup_runner $(openstack server show $VM_INFER -f value -c addresses | cut -d'=' -f2) inference
setup_runner $(openstack server show $VM_LB -f value -c addresses | cut -d'=' -f2) lb

echo "✅ Bootstrap-runner scripts deployed. Run /srv/llmops/bootstrap-runner.sh on each VM after boot."
