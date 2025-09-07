#!/bin/bash
# WireGuard Key Generation Script for Fauxdan Edge Nodes
# This script generates a WireGuard key pair for edge nodes

set -e

echo "=== WireGuard Key Generation for Fauxdan Edge Nodes ==="
echo ""

# Check if WireGuard tools are installed
if ! command -v wg &> /dev/null; then
    echo "❌ WireGuard tools not found. Please install WireGuard first:"
    echo "   sudo apt update && sudo apt install wireguard"
    exit 1
fi

# Generate private key
echo "🔑 Generating WireGuard private key..."
PRIVATE_KEY=$(wg genkey)
echo "Private Key: $PRIVATE_KEY"

# Generate public key
echo "🔑 Generating WireGuard public key..."
PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)
echo "Public Key: $PUBLIC_KEY"

echo ""
echo "=== GitLab CI Variables to Set ==="
echo ""
echo "Add these variables to your GitLab CI/CD settings:"
echo ""
echo "EDGE_PRIVATE_KEY = $PRIVATE_KEY"
echo "EDGE_PUBLIC_KEY = $PUBLIC_KEY"
echo ""
echo "=== Server Configuration ==="
echo ""
echo "Add this peer configuration to your WireGuard server:"
echo ""
echo "[Peer]"
echo "PublicKey = $PUBLIC_KEY"
echo "AllowedIPs = 10.0.0.2/32"
echo ""
echo "=== Edge Node Configuration ==="
echo ""
echo "The edge node will be configured with:"
echo "- Private Key: $PRIVATE_KEY"
echo "- Public Key: $PUBLIC_KEY"
echo "- IP Address: 10.0.0.2/24"
echo ""
echo "✅ Key generation complete!"
echo ""
echo "Next steps:"
echo "1. Set the GitLab CI variables above"
echo "2. Add the peer configuration to your WireGuard server"
echo "3. Run the GitLab CI pipeline to deploy"
