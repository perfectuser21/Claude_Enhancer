#!/bin/bash
# Fix console.log statements in production code

PRODUCTION_FILES=(
    "src/recovery/index.js"
    "src/recovery/cli/recovery-cli.js"
    "src/recovery/cli/advanced-recovery-cli.js"
    "src/recovery/ErrorRecoveryDemo.js"
)

# Backup original files
for file in "${PRODUCTION_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "${file}.console-backup"
        echo "Backed up $file"
        
        # Replace console.log with secure logging
        sed -i 's/console\.log(/logger.info(/g' "$file"
        sed -i 's/console\.warn(/logger.warn(/g' "$file"  
        sed -i 's/console\.error(/logger.error(/g' "$file"
        sed -i 's/console\.debug(/logger.debug(/g' "$file"
        
        # Add logger import if not present
        if ! grep -q "SecureLogger" "$file"; then
            sed -i '1i const SecureLogger = require("../security/SecureLogger");' "$file"
            sed -i '2i const logger = SecureLogger.getLogger("RecoverySystem");' "$file"
        fi
        
        echo "Fixed console statements in $file"
    fi
done

echo "Console.log cleanup completed for production files"
