#!/usr/bin/env node

/**
 * SecureLogger Migration Helper
 *
 * This script helps migrate existing console.log statements to use SecureLogger
 * while preserving CLI formatting and adding proper audit trails.
 */

const fs = require('fs').promises;
const path = require('path');
const { logger } = require('./SecureLogger');

class MigrationHelper {
    constructor() {
        this.patterns = {
            // CLI console patterns that need special handling
            cli: [
                /console\.log\(chalk\.[^(]*\([^)]*\)\);/g,
                /console\.error\(chalk\.[^(]*\([^)]*\)(?:, [^)]+)?\);/g,
                /console\.warn\(chalk\.[^(]*\([^)]*\)\);/g,
                /console\.info\(chalk\.[^(]*\([^)]*\)\);/g
            ],

            // Simple console patterns
            simple: [
                /console\.log\([^)]*\);/g,
                /console\.error\([^)]*\);/g,
                /console\.warn\([^)]*\);/g,
                /console\.info\([^)]*\);/g
            ]
        };

        this.stats = {
            filesProcessed: 0,
            statementsReplaced: 0,
            errors: []
        };
    }

    /**
     * Process all recovery system files
     */
    async migrateRecoveryFiles() {
        const recoveryDir = path.join(__dirname, '../recovery');
        const files = await this.findJavaScriptFiles(recoveryDir);

        logger.info('Starting SecureLogger migration', {
            totalFiles: files.length,
            directory: recoveryDir
        });

        for (const file of files) {
            try {
                await this.processFile(file);
                this.stats.filesProcessed++;
            } catch (error) {
                this.stats.errors.push({ file, error: error.message });
                logger.error('Migration error', error, { file });
            }
        }

        this.generateReport();
    }

    /**
     * Find all JavaScript files recursively
     */
    async findJavaScriptFiles(dir) {
        const files = [];
        const entries = await fs.readdir(dir, { withFileTypes: true });

        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);

            if (entry.isDirectory()) {
                const subFiles = await this.findJavaScriptFiles(fullPath);
                files.push(...subFiles);
            } else if (entry.name.endsWith('.js')) {
                files.push(fullPath);
            }
        }

        return files;
    }

    /**
     * Process individual file
     */
    async processFile(filePath) {
        const content = await fs.readFile(filePath, 'utf8');
        const originalContent = content;
        let modifiedContent = content;
        let replacementCount = 0;

        // Skip files that already use SecureLogger
        if (content.includes('SecureLogger') || content.includes('CLISecureLogger')) {
            logger.debug('File already migrated, skipping', { file: filePath });
            return;
        }

        // Determine if this is a CLI file
        const isCLI = this.isCLIFile(content);

        if (isCLI) {
            // Add CLISecureLogger import if needed
            if (!content.includes('CLISecureLogger')) {
                const importLine = "const { createCLILogger } = require('../utils/CLISecureLogger');\n";
                const insertPoint = this.findImportInsertPoint(content);
                modifiedContent = this.insertAtPosition(modifiedContent, insertPoint, importLine);
            }

            // Replace console statements with CLI logger calls
            modifiedContent = this.replaceCLIConsoleStatements(modifiedContent);
        } else {
            // Add SecureLogger import if needed
            if (!content.includes('SecureLogger')) {
                const importLine = "const { logger } = require('../utils/SecureLogger');\n";
                const insertPoint = this.findImportInsertPoint(content);
                modifiedContent = this.insertAtPosition(modifiedContent, insertPoint, importLine);
            }

            // Replace console statements with secure logger calls
            modifiedContent = this.replaceSimpleConsoleStatements(modifiedContent);
        }

        // Count replacements
        const originalMatches = this.countConsoleStatements(originalContent);
        const newMatches = this.countConsoleStatements(modifiedContent);
        replacementCount = originalMatches - newMatches;

        if (replacementCount > 0) {
            await fs.writeFile(filePath, modifiedContent);
            this.stats.statementsReplaced += replacementCount;

            logger.info('File migrated successfully', {
                file: path.relative(process.cwd(), filePath),
                replacements: replacementCount
            });
        }
    }

    /**
     * Check if file is a CLI tool
     */
    isCLIFile(content) {
        return content.includes('chalk') &&
               content.includes('Command') &&
               (content.includes('console.log') || content.includes('console.error'));
    }

    /**
     * Find appropriate position to insert import statement
     */
    findImportInsertPoint(content) {
        const lines = content.split('\n');
        let insertLine = 0;

        // Find the last require statement
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes('require(') && !lines[i].trim().startsWith('//')) {
                insertLine = i + 1;
            }
        }

        return this.getPositionFromLine(content, insertLine);
    }

    /**
     * Get character position from line number
     */
    getPositionFromLine(content, lineNumber) {
        const lines = content.split('\n');
        let position = 0;

        for (let i = 0; i < lineNumber && i < lines.length; i++) {
            position += lines[i].length + 1; // +1 for newline
        }

        return position;
    }

    /**
     * Insert text at specific position
     */
    insertAtPosition(content, position, text) {
        return content.slice(0, position) + text + content.slice(position);
    }

    /**
     * Replace CLI console statements
     */
    replaceCLIConsoleStatements(content) {
        let modified = content;

        // Add logger initialization if constructor exists
        if (content.includes('constructor(') && !content.includes('createCLILogger(')) {
            const constructorPattern = /(constructor\([^)]*\)\s*{[^}]*)/;
            modified = modified.replace(constructorPattern, (match) => {
                return match + '\n        this.cliLogger = createCLILogger(this.constructor.name);';
            });
        }

        // Replace common CLI patterns
        const replacements = [
            // console.log with chalk
            {
                pattern: /console\.log\((chalk\.[^)]+)\);/g,
                replacement: 'this.cliLogger.info("", $1);'
            },
            // console.error with chalk
            {
                pattern: /console\.error\((chalk\.[^)]+)(?:, ([^)]+))?\);/g,
                replacement: (match, chalkCall, errorVar) => {
                    if (errorVar) {
                        return `this.cliLogger.error("", ${errorVar}, ${chalkCall});`;
                    }
                    return `this.cliLogger.error("", null, ${chalkCall});`;
                }
            },
            // Simple console statements
            {
                pattern: /console\.log\(([^)]+)\);/g,
                replacement: 'this.cliLogger.info($1);'
            }
        ];

        replacements.forEach(({ pattern, replacement }) => {
            if (typeof replacement === 'function') {
                modified = modified.replace(pattern, replacement);
            } else {
                modified = modified.replace(pattern, replacement);
            }
        });

        return modified;
    }

    /**
     * Replace simple console statements
     */
    replaceSimpleConsoleStatements(content) {
        let modified = content;

        const replacements = [
            { pattern: /console\.log\(/g, replacement: 'logger.info(' },
            { pattern: /console\.error\(/g, replacement: 'logger.error(' },
            { pattern: /console\.warn\(/g, replacement: 'logger.warn(' },
            { pattern: /console\.info\(/g, replacement: 'logger.info(' },
            { pattern: /console\.debug\(/g, replacement: 'logger.debug(' }
        ];

        replacements.forEach(({ pattern, replacement }) => {
            modified = modified.replace(pattern, replacement);
        });

        return modified;
    }

    /**
     * Count console statements in content
     */
    countConsoleStatements(content) {
        const patterns = [
            /console\.log\(/g,
            /console\.error\(/g,
            /console\.warn\(/g,
            /console\.info\(/g,
            /console\.debug\(/g
        ];

        let count = 0;
        patterns.forEach(pattern => {
            const matches = content.match(pattern);
            count += matches ? matches.length : 0;
        });

        return count;
    }

    /**
     * Generate migration report
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                filesProcessed: this.stats.filesProcessed,
                statementsReplaced: this.stats.statementsReplaced,
                errorsCount: this.stats.errors.length
            },
            errors: this.stats.errors
        };

        logger.info('SecureLogger migration completed', report.summary);

        if (this.stats.errors.length > 0) {
            logger.warn('Migration completed with errors', {
                errors: this.stats.errors
            });
        }

        console.log('\n📊 Migration Report:');
        console.log(`✓ Files processed: ${report.summary.filesProcessed}`);
        console.log(`✓ Statements replaced: ${report.summary.statementsReplaced}`);
        console.log(`${report.summary.errorsCount ? '⚠' : '✓'} Errors: ${report.summary.errorsCount}`);

        return report;
    }
}

// Export for use as module
module.exports = MigrationHelper;

// Run if called directly
if (require.main === module) {
    const migrationHelper = new MigrationHelper();
    migrationHelper.migrateRecoveryFiles()
        .then(() => {
            logger.info('Migration script completed successfully');
            process.exit(0);
        })
        .catch((error) => {
            logger.error('Migration script failed', error);
            process.exit(1);
        });
}