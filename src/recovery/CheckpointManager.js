/**
 * Claude Enhancer Plus - Checkpoint Management System
 * Handles state saving, restoration, and checkpoint lifecycle
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const CryptoJS = require('crypto-js');
const { EventEmitter } = require('events');
// Try to import secure logger, but fall back to console if not available
let logger;
try {
    const { logger: secureLogger } = require('../utils/SecureLogger');
    logger = secureLogger;
} catch (error) {
    // Fallback to console logging with secure format
    logger = {
        info: (msg, context) => console.log(`INFO: ${msg}`, context || ''),
        warn: (msg, context) => console.warn(`WARN: ${msg}`, context || ''),
        error: (msg, context) => console.error(`ERROR: ${msg}`, context || ''),
        debug: (msg, context) => console.log(`DEBUG: ${msg}`, context || ''),
        security: (msg, context) => console.log(`SECURITY: ${msg}`, context || '')
    };
}

class CheckpointManager extends EventEmitter {
    constructor(options = {}) {
        super();
        this.config = {
            checkpointsDir: options.checkpointsDir || './.claude/checkpoints',
            maxCheckpoints: options.maxCheckpoints || 100,
            compressionEnabled: options.compressionEnabled || true,
            encryptionEnabled: options.encryptionEnabled !== false, // Default to true for security
            encryptionKey: options.encryptionKey || null, // Will be set after logger initialization
            retentionPeriod: options.retentionPeriod || 7 * 24 * 60 * 60 * 1000, // 7 days
            autoBackup: options.autoBackup || true,
            encryptionAlgorithm: 'AES-256-GCM',
            keyDerivationRounds: 100000,
            ...options
        };
        
        this.checkpointRegistry = new Map();
        this.activeCheckpoints = new Set();
        this.checkpointChains = new Map(); // For tracking checkpoint relationships

        // Initialize logging
        this.logger = logger;
        try {
            this.logger.info('CheckpointManager initialized', {
                checkpointsDir: this.config.checkpointsDir.replace(process.env.HOME || '', '~'),
                maxCheckpoints: this.config.maxCheckpoints,
                compressionEnabled: this.config.compressionEnabled,
                encryptionEnabled: this.config.encryptionEnabled
            });
        } catch (error) {
            console.log('CheckpointManager initialized with fallback logging');
        }
        this.encryptionCache = new Map(); // Cache for encryption keys
        this.encryptionStats = {
            encrypted: 0,
            decrypted: 0,
            encryptionErrors: 0,
            decryptionErrors: 0
        };
        
        // Set encryption key after logger is initialized
        if (!this.config.encryptionKey) {
            this.config.encryptionKey = this._generateEncryptionKeyInConstructor();
        }

        this.initializeManager();
    }
    
    /**
     * Initialize checkpoint manager
     */
    async initializeManager() {
        try {
            await this.ensureDirectories();
            await this.loadCheckpointRegistry();
            await this.performMaintenanceTasks();
            
            this.emit('managerInitialized');
        } catch (error) {
            this.emit('error', { type: 'initializationFailed', error: error.message });
            throw error;
        }
    }
    
    /**
     * Create a new checkpoint with comprehensive metadata
     */
    async createCheckpoint(id, state, options = {}) {
        const {
            description = 'Checkpoint created',
            tags = [],
            parentCheckpoint = null,
            critical = false,
            retentionOverride = null,
            metadata = {}
        } = options;
        
        try {
            // Validate checkpoint ID
            this.validateCheckpointId(id);
            
            // Check if checkpoint already exists
            if (await this.checkpointExists(id)) {
                throw new Error(`Checkpoint ${id} already exists`);
            }
            
            const checkpoint = {
                id,
                version: '2.0',
                timestamp: new Date().toISOString(),
                description,
                tags,
                parentCheckpoint,
                critical,
                retentionOverride,
                metadata: {
                    ...metadata,
                    size: this.calculateStateSize(state),
                    hash: this.calculateStateHash(state),
                    creator: process.env.USER || 'system',
                    nodeVersion: process.version,
                    platform: process.platform
                },
                state: await this.processState(state),
                encrypted: this.config.encryptionEnabled,
                encryptionVersion: this.config.encryptionEnabled ? '2.0' : null
            };
            
            // Save checkpoint to disk
            await this.saveCheckpointToDisk(checkpoint);
            
            // Update registry
            this.checkpointRegistry.set(id, {
                id,
                timestamp: checkpoint.timestamp,
                description,
                tags,
                parentCheckpoint,
                critical,
                metadata: checkpoint.metadata
            });
            
            this.activeCheckpoints.add(id);
            
            // Update checkpoint chains
            if (parentCheckpoint) {
                this.updateCheckpointChain(parentCheckpoint, id);
            }
            
            // Emit event
            this.emit('checkpointCreated', { 
                checkpointId: id, 
                metadata: checkpoint.metadata 
            });
            
            // Cleanup old checkpoints if needed
            await this.enforceRetentionPolicy();
            
            return checkpoint;
            
        } catch (error) {
            this.emit('error', { 
                type: 'checkpointCreationFailed', 
                checkpointId: id, 
                error: error.message 
            });
            throw new Error(`Failed to create checkpoint ${id}: ${error.message}`);
        }
    }
    
    /**
     * Get checkpoint statistics
     */
    async getStatistics() {
        try {
            const checkpoints = Array.from(this.checkpointRegistry.values());
            const chains = Array.from(this.checkpointChains.values());
            
            const totalSize = checkpoints.reduce((sum, cp) => sum + (cp.metadata.size || 0), 0);
            const criticalCount = checkpoints.filter(cp => cp.critical).length;
            const tagCounts = {};
            
            // Count tags
            checkpoints.forEach(cp => {
                cp.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            });
            
            return {
                totalCheckpoints: checkpoints.length,
                totalChains: chains.length,
                activeCheckpoints: this.activeCheckpoints.size,
                criticalCheckpoints: criticalCount,
                totalSize,
                averageSize: checkpoints.length > 0 ? totalSize / checkpoints.length : 0,
                tagCounts
            };
            
        } catch (error) {
            throw new Error(`Failed to get statistics: ${error.message}`);
        }
    }
    
    // Helper methods
    validateCheckpointId(id) {
        if (!id || typeof id !== 'string') {
            throw new Error('Checkpoint ID must be a non-empty string');
        }
    }
    
    async checkpointExists(id) {
        try {
            const checkpointPath = path.join(this.config.checkpointsDir, `${id}.json`);
            await fs.access(checkpointPath);
            return true;
        } catch (error) {
            return false;
        }
    }
    
    calculateStateSize(state) {
        return Buffer.byteLength(JSON.stringify(state), 'utf8');
    }
    
    calculateStateHash(state) {
        return crypto.createHash('sha256').update(JSON.stringify(state)).digest('hex');
    }
    
    async processState(state) {
        const stateJson = JSON.stringify(state);

        if (this.config.encryptionEnabled) {
            try {
                const encrypted = await this.encryptData(stateJson);
                this.encryptionStats.encrypted++;
                return encrypted;
            } catch (error) {
                this.encryptionStats.encryptionErrors++;
                this.emit('error', {
                    type: 'encryptionFailed',
                    error: error.message,
                    fallback: 'saving unencrypted'
                });
                // Fallback to unencrypted if encryption fails
                return stateJson;
            }
        }

        return stateJson;
    }
    
    async saveCheckpointToDisk(checkpoint) {
        const checkpointPath = path.join(this.config.checkpointsDir, `${checkpoint.id}.json`);

        try {
            const checkpointData = JSON.stringify(checkpoint, null, 2);
            await fs.writeFile(checkpointPath, checkpointData, { mode: 0o600 }); // Restrict permissions

            this.emit('checkpointSaved', {
                checkpointId: checkpoint.id,
                path: checkpointPath,
                encrypted: checkpoint.encrypted || false,
                size: Buffer.byteLength(checkpointData)
            });

        } catch (error) {
            this.emit('error', {
                type: 'checkpointSaveFailed',
                checkpointId: checkpoint.id,
                error: error.message
            });
            throw error;
        }
    }
    
    async ensureDirectories() {
        await fs.mkdir(this.config.checkpointsDir, { recursive: true });
    }
    
    // This method is now implemented in the enhanced version below
    // async loadCheckpointRegistry() {
    //     // This is replaced by the enhanced implementation below
    // }
    
    async performMaintenanceTasks() {
        // Basic maintenance
        await this.enforceRetentionPolicy();
    }
    
    async enforceRetentionPolicy() {
        // Basic retention policy
        if (this.checkpointRegistry.size <= this.config.maxCheckpoints) {
            return;
        }
    }
    
    updateCheckpointChain(parentId, childId) {
        // Basic chain management
        const chainId = `chain_${parentId}`;
        if (!this.checkpointChains.has(chainId)) {
            this.checkpointChains.set(chainId, [parentId]);
        }
        this.checkpointChains.get(chainId).push(childId);
    }

    // ===== ENCRYPTION METHODS =====

    /**
     * Generate or retrieve encryption key from environment (constructor version)
     */
    _generateEncryptionKeyInConstructor() {
        // Try to get key from environment first
        let key = process.env.PERFECT21_CHECKPOINT_KEY ||
                 process.env.CHECKPOINT_ENCRYPTION_KEY ||
                 process.env.ENCRYPTION_KEY;

        if (!key) {
            // Generate a random key
            key = crypto.randomBytes(32).toString('hex');
            console.log('Warning: No encryption key found in environment. Generated random key. Set PERFECT21_CHECKPOINT_KEY to persist across restarts.');
            console.log(`Suggestion: export PERFECT21_CHECKPOINT_KEY="${key}"`);
        }

        return key;
    }

    /**
     * Generate or retrieve encryption key from environment
     */
    generateEncryptionKey() {
        // Try to get key from environment first
        let key = process.env.PERFECT21_CHECKPOINT_KEY ||
                 process.env.CHECKPOINT_ENCRYPTION_KEY ||
                 process.env.ENCRYPTION_KEY;

        if (!key) {
            // Generate a random key and warn user
            key = crypto.randomBytes(32).toString('hex');
            try {
                this.logger.warn('No encryption key found in environment', {
                    message: 'Generated random key. Set PERFECT21_CHECKPOINT_KEY to persist across restarts.',
                    suggestion: `export PERFECT21_CHECKPOINT_KEY="${key}"`
                });
            } catch (e) {
                console.warn('No encryption key found in environment. Generated random key.');
            }

            this.emit('warning', {
                type: 'generatedEncryptionKey',
                message: 'No encryption key found in environment. Generated random key. Set PERFECT21_CHECKPOINT_KEY to persist across restarts.',
                suggestion: `export PERFECT21_CHECKPOINT_KEY="${key}"`
            });
        } else {
            try {
                this.logger.info('Using encryption key from environment');
            } catch (e) {
                console.log('Using encryption key from environment');
            }
        }

        return key;
    }

    /**
     * Derive encryption key using PBKDF2
     */
    deriveKey(password, salt) {
        return crypto.pbkdf2Sync(
            password,
            salt,
            this.config.keyDerivationRounds,
            32, // 256 bits
            'sha256'
        );
    }

    /**
     * Encrypt data using AES-256-GCM
     */
    async encryptData(data) {
        try {
            // Generate random salt and IV
            const salt = crypto.randomBytes(16);
            const iv = crypto.randomBytes(16);

            // Derive key from master key and salt
            const derivedKey = this.deriveKey(this.config.encryptionKey, salt);

            // Create cipher using the modern API
            const cipher = crypto.createCipheriv('aes-256-gcm', derivedKey, iv);
            cipher.setAAD(Buffer.from('perfect21-checkpoint'));

            // Encrypt data
            const encrypted = Buffer.concat([
                cipher.update(data, 'utf8'),
                cipher.final()
            ]);

            // Get authentication tag
            const authTag = cipher.getAuthTag();

            // Combine all components
            const result = {
                encrypted: encrypted.toString('hex'),
                salt: salt.toString('hex'),
                iv: iv.toString('hex'),
                authTag: authTag.toString('hex'),
                algorithm: 'aes-256-gcm',
                timestamp: Date.now()
            };

            try {
                this.logger.debug('Data encrypted successfully', {
                    algorithm: result.algorithm,
                    dataSize: Buffer.byteLength(data, 'utf8'),
                    encryptedSize: Buffer.byteLength(JSON.stringify(result), 'utf8')
                });
            } catch (e) {
                // Fallback logging
            }

            return JSON.stringify(result);

        } catch (error) {
            try {
                this.logger.error('Encryption failed', { error: error.message });
            } catch (e) {
                console.error('Encryption failed:', error.message);
            }
            throw new Error(`Encryption failed: ${error.message}`);
        }
    }

    /**
     * Decrypt data using AES-256-GCM
     */
    async decryptData(encryptedData) {
        try {
            // Parse encrypted data
            let parsedData;
            try {
                parsedData = JSON.parse(encryptedData);
            } catch (parseError) {
                // Data might not be encrypted - return as is for backward compatibility
                try {
                    this.logger.debug('Data appears to be unencrypted, returning as-is for backward compatibility');
                } catch (e) {
                    // Fallback logging
                }
                return encryptedData;
            }

            // Check if data has encryption structure
            if (!parsedData.encrypted || !parsedData.salt) {
                // Not encrypted data - return as is
                try {
                    this.logger.debug('Data structure does not indicate encryption, returning as-is');
                } catch (e) {
                    // Fallback logging
                }
                return encryptedData;
            }

            // Extract components
            const { encrypted, salt, iv, authTag, algorithm } = parsedData;

            // Derive key from master key and salt
            const derivedKey = this.deriveKey(
                this.config.encryptionKey,
                Buffer.from(salt, 'hex')
            );

            // Create decipher using modern API
            const decipher = crypto.createDecipheriv('aes-256-gcm', derivedKey, Buffer.from(iv, 'hex'));
            decipher.setAAD(Buffer.from('perfect21-checkpoint'));
            if (authTag) {
                decipher.setAuthTag(Buffer.from(authTag, 'hex'));
            }

            // Decrypt data
            const decrypted = Buffer.concat([
                decipher.update(Buffer.from(encrypted, 'hex')),
                decipher.final()
            ]).toString('utf8');

            this.encryptionStats.decrypted++;
            try {
                this.logger.debug('Data decrypted successfully', {
                    algorithm: algorithm || 'aes-256-gcm',
                    decryptedSize: Buffer.byteLength(decrypted, 'utf8')
                });
            } catch (e) {
                // Fallback logging
            }

            return decrypted;

        } catch (error) {
            this.encryptionStats.decryptionErrors++;
            try {
                this.logger.error('Decryption failed', { error: error.message });
            } catch (e) {
                console.error('Decryption failed:', error.message);
            }
            throw new Error(`Decryption failed: ${error.message}`);
        }
    }

    // ===== MISSING CORE METHODS =====

    /**
     * Restore checkpoint from disk
     */
    async restoreCheckpoint(checkpointId) {
        try {
            // Validate checkpoint ID
            this.validateCheckpointId(checkpointId);

            this.logger.info('Restoring checkpoint', { checkpointId });

            // Check if checkpoint exists in registry
            const registryEntry = this.checkpointRegistry.get(checkpointId);
            if (!registryEntry) {
                throw new Error(`Checkpoint ${checkpointId} not found in registry`);
            }

            // Read checkpoint file
            const checkpointPath = path.join(this.config.checkpointsDir, `${checkpointId}.json`);
            const fileContent = await fs.readFile(checkpointPath, 'utf8');
            const checkpoint = JSON.parse(fileContent);

            // Decrypt state if encrypted
            let state;
            if (checkpoint.encrypted) {
                try {
                    const decryptedState = await this.decryptData(checkpoint.state);
                    state = JSON.parse(decryptedState);
                    this.logger.debug('Checkpoint state decrypted', { checkpointId });
                } catch (decryptError) {
                    this.logger.error('Checkpoint decryption failed', {
                        checkpointId,
                        error: decryptError.message
                    });
                    this.emit('error', {
                        type: 'decryptionFailed',
                        checkpointId,
                        error: decryptError.message
                    });
                    throw new Error(`Failed to decrypt checkpoint ${checkpointId}: ${decryptError.message}`);
                }
            } else {
                // Handle unencrypted checkpoints (backward compatibility)
                state = typeof checkpoint.state === 'string' ?
                       JSON.parse(checkpoint.state) :
                       checkpoint.state;
                this.logger.debug('Restored unencrypted checkpoint', { checkpointId });
            }

            // Update metrics
            if (!this.metrics) {
                this.metrics = {};
            }
            this.metrics.checkpointsRestored = (this.metrics.checkpointsRestored || 0) + 1;

            // Emit event
            this.emit('checkpointRestored', {
                checkpointId,
                encrypted: checkpoint.encrypted || false,
                timestamp: checkpoint.timestamp,
                metadata: checkpoint.metadata
            });

            this.logger.info('Checkpoint restored successfully', {
                checkpointId,
                encrypted: checkpoint.encrypted || false,
                stateSize: JSON.stringify(state).length
            });

            return {
                id: checkpoint.id,
                state,
                metadata: checkpoint.metadata,
                timestamp: checkpoint.timestamp,
                description: checkpoint.description,
                tags: checkpoint.tags || [],
                encrypted: checkpoint.encrypted || false
            };

        } catch (error) {
            this.logger.error('Checkpoint restore failed', {
                checkpointId,
                error: error.message
            });
            this.emit('error', {
                type: 'checkpointRestoreFailed',
                checkpointId,
                error: error.message
            });
            throw new Error(`Failed to restore checkpoint ${checkpointId}: ${error.message}`);
        }
    }

    /**
     * List all checkpoints with optional filtering
     */
    async listCheckpoints(options = {}) {
        try {
            const {
                tags = [],
                critical = null,
                encrypted = null,
                sortBy = 'timestamp',
                sortOrder = 'desc',
                limit = null,
                includeState = false
            } = options;

            this.logger.debug('Listing checkpoints', { options });

            let checkpoints = Array.from(this.checkpointRegistry.values());

            // Apply filters
            if (tags.length > 0) {
                checkpoints = checkpoints.filter(cp =>
                    tags.some(tag => cp.tags && cp.tags.includes(tag))
                );
            }

            if (critical !== null) {
                checkpoints = checkpoints.filter(cp => cp.critical === critical);
            }

            if (encrypted !== null) {
                checkpoints = checkpoints.filter(cp => cp.encrypted === encrypted);
            }

            // Sort checkpoints
            checkpoints.sort((a, b) => {
                let aVal = a[sortBy];
                let bVal = b[sortBy];

                if (sortBy === 'timestamp') {
                    aVal = new Date(aVal).getTime();
                    bVal = new Date(bVal).getTime();
                }

                if (sortOrder === 'desc') {
                    return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
                } else {
                    return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
                }
            });

            // Apply limit
            if (limit && limit > 0) {
                checkpoints = checkpoints.slice(0, limit);
            }

            // Include state if requested
            if (includeState) {
                const checkpointsWithState = [];
                for (const cp of checkpoints) {
                    try {
                        const restored = await this.restoreCheckpoint(cp.id);
                        checkpointsWithState.push({
                            ...cp,
                            state: restored.state
                        });
                    } catch (error) {
                        checkpointsWithState.push({
                            ...cp,
                            stateError: error.message
                        });
                    }
                }
                return checkpointsWithState;
            }

            this.logger.info('Checkpoints listed', {
                totalFound: checkpoints.length,
                filtered: {
                    tags: tags.length > 0,
                    critical: critical !== null,
                    encrypted: encrypted !== null
                }
            });

            return checkpoints;

        } catch (error) {
            this.logger.error('List checkpoints failed', { error: error.message });
            this.emit('error', {
                type: 'listCheckpointsFailed',
                error: error.message
            });
            throw new Error(`Failed to list checkpoints: ${error.message}`);
        }
    }

    /**
     * Delete checkpoint
     */
    async deleteCheckpoint(checkpointId, options = {}) {
        try {
            this.validateCheckpointId(checkpointId);

            const { force = false, cleanupChain = true } = options;

            this.logger.info('Deleting checkpoint', { checkpointId, force, cleanupChain });

            // Check if checkpoint exists
            if (!this.checkpointRegistry.has(checkpointId)) {
                throw new Error(`Checkpoint ${checkpointId} not found`);
            }

            const checkpoint = this.checkpointRegistry.get(checkpointId);

            // Check if critical checkpoint
            if (checkpoint.critical && !force) {
                throw new Error(`Cannot delete critical checkpoint ${checkpointId}. Use force=true to override.`);
            }

            // Delete file
            const checkpointPath = path.join(this.config.checkpointsDir, `${checkpointId}.json`);
            try {
                await fs.unlink(checkpointPath);
                this.logger.debug('Checkpoint file deleted', { path: checkpointPath });
            } catch (fileError) {
                if (fileError.code !== 'ENOENT') {
                    throw fileError;
                }
            }

            // Remove from registry and active set
            this.checkpointRegistry.delete(checkpointId);
            this.activeCheckpoints.delete(checkpointId);

            // Cleanup checkpoint chains if requested
            if (cleanupChain) {
                for (const [chainId, chain] of this.checkpointChains.entries()) {
                    const index = chain.indexOf(checkpointId);
                    if (index !== -1) {
                        chain.splice(index, 1);
                        if (chain.length === 0) {
                            this.checkpointChains.delete(chainId);
                        }
                    }
                }
            }

            this.emit('checkpointDeleted', {
                checkpointId,
                critical: checkpoint.critical,
                encrypted: checkpoint.encrypted
            });

            this.logger.info('Checkpoint deleted successfully', {
                checkpointId,
                critical: checkpoint.critical,
                encrypted: checkpoint.encrypted
            });

            return { success: true, checkpointId };

        } catch (error) {
            this.logger.error('Checkpoint delete failed', {
                checkpointId,
                error: error.message
            });
            this.emit('error', {
                type: 'checkpointDeleteFailed',
                checkpointId,
                error: error.message
            });
            throw new Error(`Failed to delete checkpoint ${checkpointId}: ${error.message}`);
        }
    }

    /**
     * Clean up old checkpoints based on retention policy
     */
    async cleanupCheckpoints(options = {}) {
        try {
            const { dryRun = false, preserveCritical = true } = options;
            const now = Date.now();
            const deletedCheckpoints = [];
            const preservedCheckpoints = [];

            this.logger.info('Starting checkpoint cleanup', { dryRun, preserveCritical });

            for (const [checkpointId, checkpoint] of this.checkpointRegistry.entries()) {
                const checkpointTime = new Date(checkpoint.timestamp).getTime();
                const age = now - checkpointTime;
                const retentionPeriod = checkpoint.retentionOverride || this.config.retentionPeriod;

                // Check if checkpoint should be deleted
                const shouldDelete = age > retentionPeriod &&
                                   (!preserveCritical || !checkpoint.critical);

                if (shouldDelete) {
                    if (!dryRun) {
                        try {
                            await this.deleteCheckpoint(checkpointId, { force: true });
                            deletedCheckpoints.push({
                                id: checkpointId,
                                age: Math.round(age / (1000 * 60 * 60)), // hours
                                critical: checkpoint.critical
                            });
                        } catch (deleteError) {
                            this.logger.warn('Cleanup delete failed', {
                                checkpointId,
                                error: deleteError.message
                            });
                            this.emit('warning', {
                                type: 'cleanupDeleteFailed',
                                checkpointId,
                                error: deleteError.message
                            });
                        }
                    } else {
                        deletedCheckpoints.push({
                            id: checkpointId,
                            age: Math.round(age / (1000 * 60 * 60)), // hours
                            critical: checkpoint.critical
                        });
                    }
                } else {
                    preservedCheckpoints.push({
                        id: checkpointId,
                        age: Math.round(age / (1000 * 60 * 60)), // hours
                        reason: checkpoint.critical ? 'critical' : 'within-retention'
                    });
                }
            }

            this.emit('cleanupCompleted', {
                deletedCount: deletedCheckpoints.length,
                preservedCount: preservedCheckpoints.length,
                dryRun
            });

            this.logger.info('Checkpoint cleanup completed', {
                deletedCount: deletedCheckpoints.length,
                preservedCount: preservedCheckpoints.length,
                dryRun
            });

            return {
                deleted: deletedCheckpoints,
                preserved: preservedCheckpoints,
                totalProcessed: deletedCheckpoints.length + preservedCheckpoints.length,
                dryRun
            };

        } catch (error) {
            this.logger.error('Cleanup failed', { error: error.message });
            this.emit('error', {
                type: 'cleanupFailed',
                error: error.message
            });
            throw new Error(`Cleanup failed: ${error.message}`);
        }
    }

    /**
     * Get encryption statistics and key information
     */
    getEncryptionInfo() {
        return {
            encryptionEnabled: this.config.encryptionEnabled,
            algorithm: this.config.encryptionAlgorithm,
            keySource: process.env.PERFECT21_CHECKPOINT_KEY ? 'environment' : 'generated',
            stats: { ...this.encryptionStats },
            encryptedCheckpoints: Array.from(this.checkpointRegistry.values())
                .filter(cp => cp.encrypted).length,
            totalCheckpoints: this.checkpointRegistry.size
        };
    }

    /**
     * Migrate existing checkpoints to encrypted format
     */
    async migrateToEncrypted(options = {}) {
        try {
            const { dryRun = false, batchSize = 10 } = options;
            const unencryptedCheckpoints = Array.from(this.checkpointRegistry.values())
                .filter(cp => !cp.encrypted);

            this.logger.info('Starting checkpoint encryption migration', {
                totalUnencrypted: unencryptedCheckpoints.length,
                dryRun,
                batchSize
            });

            if (unencryptedCheckpoints.length === 0) {
                return {
                    migrated: [],
                    totalProcessed: 0,
                    message: 'All checkpoints are already encrypted'
                };
            }

            const migrated = [];
            const failed = [];

            // Process in batches
            for (let i = 0; i < unencryptedCheckpoints.length; i += batchSize) {
                const batch = unencryptedCheckpoints.slice(i, i + batchSize);
                this.logger.debug('Processing migration batch', {
                    batchIndex: Math.floor(i / batchSize) + 1,
                    batchSize: batch.length
                });

                for (const checkpointInfo of batch) {
                    try {
                        if (!dryRun) {
                            // Restore the checkpoint
                            const checkpoint = await this.restoreCheckpoint(checkpointInfo.id);

                            // Re-save with encryption enabled
                            const tempEncryptionState = this.config.encryptionEnabled;
                            this.config.encryptionEnabled = true;

                            const updatedCheckpoint = {
                                ...checkpointInfo,
                                state: await this.processState(checkpoint.state),
                                encrypted: true,
                                encryptionVersion: '2.0'
                            };

                            await this.saveCheckpointToDisk(updatedCheckpoint);

                            // Restore original encryption setting
                            this.config.encryptionEnabled = tempEncryptionState;

                            // Update registry
                            this.checkpointRegistry.set(checkpointInfo.id, {
                                ...checkpointInfo,
                                encrypted: true,
                                encryptionVersion: '2.0'
                            });
                        }

                        migrated.push({
                            id: checkpointInfo.id,
                            originalSize: checkpointInfo.metadata?.size || 0
                        });

                    } catch (error) {
                        this.logger.error('Migration failed for checkpoint', {
                            checkpointId: checkpointInfo.id,
                            error: error.message
                        });
                        failed.push({
                            id: checkpointInfo.id,
                            error: error.message
                        });
                    }
                }

                // Small delay between batches
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            this.emit('migrationCompleted', {
                migratedCount: migrated.length,
                failedCount: failed.length,
                dryRun
            });

            this.logger.info('Migration completed', {
                migratedCount: migrated.length,
                failedCount: failed.length,
                dryRun
            });

            return {
                migrated,
                failed,
                totalProcessed: migrated.length + failed.length,
                dryRun
            };

        } catch (error) {
            this.logger.error('Migration failed', { error: error.message });
            this.emit('error', {
                type: 'migrationFailed',
                error: error.message
            });
            throw new Error(`Migration failed: ${error.message}`);
        }
    }

    /**
     * Enhanced registry loading with encryption support
     */
    async loadCheckpointRegistry() {
        try {
            // Clear existing registry
            this.checkpointRegistry.clear();
            this.logger.info('Loading checkpoint registry');

            // Ensure directory exists
            await this.ensureDirectories();

            // Load all checkpoint files
            const files = await fs.readdir(this.config.checkpointsDir);
            const jsonFiles = files.filter(file => file.endsWith('.json'));

            this.logger.debug('Found checkpoint files', { count: jsonFiles.length });

            for (const file of jsonFiles) {
                try {
                    const filePath = path.join(this.config.checkpointsDir, file);
                    const fileContent = await fs.readFile(filePath, 'utf8');
                    const checkpoint = JSON.parse(fileContent);

                    // Register checkpoint metadata
                    this.checkpointRegistry.set(checkpoint.id, {
                        id: checkpoint.id,
                        timestamp: checkpoint.timestamp,
                        description: checkpoint.description || 'No description',
                        tags: checkpoint.tags || [],
                        parentCheckpoint: checkpoint.parentCheckpoint,
                        critical: checkpoint.critical || false,
                        encrypted: checkpoint.encrypted || false,
                        encryptionVersion: checkpoint.encryptionVersion,
                        metadata: checkpoint.metadata || {},
                        filePath
                    });

                    this.activeCheckpoints.add(checkpoint.id);

                } catch (fileError) {
                    this.logger.warn('Failed to load checkpoint file', {
                        file,
                        error: fileError.message
                    });
                    this.emit('warning', {
                        type: 'checkpointLoadFailed',
                        file,
                        error: fileError.message
                    });
                }
            }

            this.emit('registryLoaded', {
                totalCheckpoints: this.checkpointRegistry.size
            });

            this.logger.info('Checkpoint registry loaded', {
                totalCheckpoints: this.checkpointRegistry.size,
                encryptedCount: Array.from(this.checkpointRegistry.values())
                    .filter(cp => cp.encrypted).length
            });

        } catch (error) {
            this.logger.error('Registry load failed', { error: error.message });
            this.emit('error', {
                type: 'registryLoadFailed',
                error: error.message
            });
            // Don't throw - allow system to work with empty registry
        }
    }

    /**
     * Enhanced retention policy with encryption awareness
     */
    async enforceRetentionPolicy() {
        try {
            if (this.checkpointRegistry.size <= this.config.maxCheckpoints) {
                return { action: 'none', reason: 'within limits' };
            }

            this.logger.info('Enforcing retention policy', {
                currentCount: this.checkpointRegistry.size,
                maxCheckpoints: this.config.maxCheckpoints
            });

            // Get checkpoints sorted by age (oldest first)
            const checkpoints = Array.from(this.checkpointRegistry.values())
                .filter(cp => !cp.critical) // Never delete critical checkpoints
                .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

            const excess = this.checkpointRegistry.size - this.config.maxCheckpoints;
            const toDelete = checkpoints.slice(0, excess);

            this.logger.debug('Retention policy enforcement', {
                excess,
                toDeleteCount: toDelete.length,
                criticalPreserved: Array.from(this.checkpointRegistry.values())
                    .filter(cp => cp.critical).length
            });

            let deleted = 0;
            for (const checkpoint of toDelete) {
                try {
                    await this.deleteCheckpoint(checkpoint.id, { force: false });
                    deleted++;
                } catch (error) {
                    this.logger.warn('Failed to delete checkpoint during retention enforcement', {
                        checkpointId: checkpoint.id,
                        error: error.message
                    });
                }
            }

            this.logger.info('Retention policy enforced', {
                deletedCount: deleted,
                remainingCount: this.checkpointRegistry.size
            });

            return {
                action: 'cleanup',
                deletedCount: deleted,
                remainingCount: this.checkpointRegistry.size
            };

        } catch (error) {
            this.logger.error('Retention policy enforcement failed', {
                error: error.message
            });
            return { action: 'error', error: error.message };
        }
    }
}

module.exports = CheckpointManager;
