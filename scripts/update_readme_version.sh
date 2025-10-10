#!/bin/bash
# Update README.md version badge
sed -i 's/version-5\.1\.1-blue/version-5.3.4-blue/' /home/xx/dev/Claude\ Enhancer\ 5.0/README.md
sed -i 's/# Claude Enhancer 5\.1\.1/# Claude Enhancer 5.3.4/' /home/xx/dev/Claude\ Enhancer\ 5.0/README.md
echo "✓ Updated README.md version to 5.3.4"
