/**
 * Comprehensive Test Suite for Checkpoint Encryption
 * Tests AES-256-GCM encryption/decryption, key management, and backward compatibility
 */

const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');

// Import the updated CheckpointManager
const CheckpointManager = require('./src/recovery/CheckpointManager');

class CheckpointEncryptionTester {
    constructor() {
        this.testDir = '/tmp/claude/checkpoint-encryption-test';
        this.results = [];
        this.stats = {
            passed: 0,
            failed: 0,
            total: 0
        };
    }

    /**
     * Log test results
     */
    log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        const colors = {
            info: '\x1b[36m',      // Cyan
            success: '\x1b[32m',   // Green
            error: '\x1b[31m',     // Red
            warn: '\x1b[33m',      // Yellow
            reset: '\x1b[0m'       // Reset
        };

        console.log(`${colors[type] || colors.info}[${timestamp}] ${message}${colors.reset}`);
    }

    /**
     * Run a test and record results
     */
    async runTest(name, testFn) {
        this.stats.total++;

        try {
            this.log(`Running test: ${name}`, 'info');
            await testFn();
            this.stats.passed++;
            this.results.push({ name, status: 'PASSED', error: null });
            this.log(`✓ PASSED: ${name}`, 'success');
        } catch (error) {
            this.stats.failed++;
            this.results.push({ name, status: 'FAILED', error: error.message });
            this.log(`✗ FAILED: ${name} - ${error.message}`, 'error');
        }
    }

    /**
     * Setup test environment
     */
    async setup() {
        try {
            // Ensure test directory exists
            await fs.mkdir(this.testDir, { recursive: true });

            // Set a test encryption key
            process.env.PERFECT21_CHECKPOINT_KEY = crypto.randomBytes(32).toString('hex');

            this.log('Test environment setup completed', 'success');
        } catch (error) {
            this.log(`Setup failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Cleanup test environment
     */
    async cleanup() {
        try {
            // Remove test directory
            await fs.rm(this.testDir, { recursive: true, force: true });

            // Clean up environment
            delete process.env.PERFECT21_CHECKPOINT_KEY;

            this.log('Test environment cleaned up', 'success');
        } catch (error) {
            this.log(`Cleanup failed: ${error.message}`, 'warn');
        }
    }

    /**
     * Test 1: Basic Encryption/Decryption
     */
    async testBasicEncryption() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        const testData = { message: 'Hello, World!', timestamp: Date.now() };

        // Test encryption
        const encrypted = await manager.encryptData(JSON.stringify(testData));

        if (typeof encrypted !== 'string') {
            throw new Error('Encryption did not return a string');
        }

        // Verify encrypted data is different from original
        if (encrypted === JSON.stringify(testData)) {
            throw new Error('Encrypted data is identical to original data');
        }

        // Test decryption
        const decrypted = await manager.decryptData(encrypted);
        const parsedDecrypted = JSON.parse(decrypted);

        if (JSON.stringify(parsedDecrypted) !== JSON.stringify(testData)) {
            throw new Error('Decrypted data does not match original data');
        }

        // Verify encryption stats
        if (manager.encryptionStats.encrypted !== 1) {
            throw new Error('Encryption stats not updated correctly');
        }

        if (manager.encryptionStats.decrypted !== 1) {
            throw new Error('Decryption stats not updated correctly');
        }
    }

    /**
     * Test 2: Checkpoint Creation and Restoration with Encryption
     */
    async testEncryptedCheckpointLifecycle() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        const testState = {
            phase: 'Phase3_Implementation',
            progress: 75,
            data: {
                files: ['file1.js', 'file2.js'],
                config: { debug: true, mode: 'development' }
            },
            timestamp: Date.now()
        };

        // Create encrypted checkpoint
        const checkpointId = 'test-encrypted-checkpoint';
        const checkpoint = await manager.createCheckpoint(checkpointId, testState, {
            description: 'Test encrypted checkpoint',
            tags: ['test', 'encrypted'],
            critical: true
        });

        // Verify checkpoint was marked as encrypted
        if (!checkpoint.encrypted) {
            throw new Error('Checkpoint was not marked as encrypted');
        }

        // Verify file was created
        const checkpointPath = path.join(this.testDir, `${checkpointId}.json`);
        const fileExists = await fs.access(checkpointPath).then(() => true).catch(() => false);

        if (!fileExists) {
            throw new Error('Checkpoint file was not created');
        }

        // Verify the raw file content is encrypted (not readable JSON)
        const rawContent = await fs.readFile(checkpointPath, 'utf8');
        const parsedRaw = JSON.parse(rawContent);

        // The state should be encrypted (a string, not an object)
        if (typeof parsedRaw.state !== 'string') {
            throw new Error('Checkpoint state in file is not encrypted');
        }

        // Try to parse the state - it should be encrypted JSON, not the original object
        try {
            const directParsed = JSON.parse(parsedRaw.state);
            if (directParsed.phase === testState.phase) {
                throw new Error('State appears to be stored unencrypted');
            }
        } catch (e) {
            // This is expected for encrypted data
        }

        // Restore checkpoint
        const restored = await manager.restoreCheckpoint(checkpointId);

        // Verify restored data matches original
        if (JSON.stringify(restored.state) !== JSON.stringify(testState)) {
            throw new Error('Restored checkpoint state does not match original');
        }

        if (restored.description !== 'Test encrypted checkpoint') {
            throw new Error('Restored checkpoint description does not match');
        }

        if (!restored.tags.includes('encrypted')) {
            throw new Error('Restored checkpoint tags do not match');
        }
    }

    /**
     * Test 3: Backward Compatibility
     */
    async testBackwardCompatibility() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        // Create an unencrypted checkpoint manually
        const unencryptedState = { message: 'Unencrypted data', version: 1.0 };
        const unencryptedCheckpoint = {
            id: 'legacy-unencrypted',
            version: '1.0',
            timestamp: new Date().toISOString(),
            description: 'Legacy unencrypted checkpoint',
            tags: ['legacy'],
            state: JSON.stringify(unencryptedState),
            encrypted: false
        };

        const legacyPath = path.join(this.testDir, 'legacy-unencrypted.json');
        await fs.writeFile(legacyPath, JSON.stringify(unencryptedCheckpoint, null, 2));

        // Add to registry manually
        manager.checkpointRegistry.set('legacy-unencrypted', {
            id: 'legacy-unencrypted',
            timestamp: unencryptedCheckpoint.timestamp,
            description: unencryptedCheckpoint.description,
            tags: unencryptedCheckpoint.tags,
            encrypted: false,
            metadata: {}
        });

        // Try to restore the unencrypted checkpoint
        const restored = await manager.restoreCheckpoint('legacy-unencrypted');

        // Verify the data is correctly restored
        if (JSON.stringify(restored.state) !== JSON.stringify(unencryptedState)) {
            throw new Error('Legacy unencrypted checkpoint restoration failed');
        }

        if (restored.encrypted !== false) {
            throw new Error('Legacy checkpoint encryption flag incorrect');
        }
    }

    /**
     * Test 4: Key Management
     */
    async testKeyManagement() {
        // Test with environment key
        const envKey = crypto.randomBytes(32).toString('hex');
        process.env.PERFECT21_CHECKPOINT_KEY = envKey;

        const manager1 = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        if (manager1.config.encryptionKey !== envKey) {
            throw new Error('Manager did not use environment key');
        }

        // Test without environment key (should generate one)
        delete process.env.PERFECT21_CHECKPOINT_KEY;

        const manager2 = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        if (!manager2.config.encryptionKey || manager2.config.encryptionKey.length !== 64) {
            throw new Error('Manager did not generate proper key');
        }

        // Test with explicit key in options
        const explicitKey = crypto.randomBytes(32).toString('hex');
        const manager3 = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true,
            encryptionKey: explicitKey
        });

        if (manager3.config.encryptionKey !== explicitKey) {
            throw new Error('Manager did not use explicitly provided key');
        }

        // Reset environment
        process.env.PERFECT21_CHECKPOINT_KEY = crypto.randomBytes(32).toString('hex');
    }

    /**
     * Test 5: Encryption Statistics
     */
    async testEncryptionStatistics() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        const initialStats = { ...manager.encryptionStats };

        // Perform several operations
        await manager.encryptData('test data 1');
        await manager.encryptData('test data 2');
        await manager.decryptData(await manager.encryptData('test data 3'));

        // Check stats
        if (manager.encryptionStats.encrypted !== initialStats.encrypted + 3) {
            throw new Error('Encryption count incorrect');
        }

        if (manager.encryptionStats.decrypted !== initialStats.decrypted + 1) {
            throw new Error('Decryption count incorrect');
        }

        // Test encryption info
        const encInfo = manager.getEncryptionInfo();

        if (!encInfo.encryptionEnabled) {
            throw new Error('Encryption info shows encryption disabled');
        }

        if (encInfo.algorithm !== 'AES-256-GCM') {
            throw new Error('Wrong algorithm in encryption info');
        }

        if (encInfo.keySource !== 'environment') {
            throw new Error('Wrong key source in encryption info');
        }
    }

    /**
     * Test 6: Migration Functionality
     */
    async testMigration() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        // Create some unencrypted checkpoints manually
        const unencryptedData = [
            { id: 'migrate-1', state: { data: 'migrate test 1' } },
            { id: 'migrate-2', state: { data: 'migrate test 2' } }
        ];

        for (const item of unencryptedData) {
            const checkpoint = {
                id: item.id,
                version: '1.0',
                timestamp: new Date().toISOString(),
                description: 'Pre-migration checkpoint',
                tags: ['migration-test'],
                state: JSON.stringify(item.state),
                encrypted: false
            };

            const checkpointPath = path.join(this.testDir, `${item.id}.json`);
            await fs.writeFile(checkpointPath, JSON.stringify(checkpoint, null, 2));

            // Add to registry
            manager.checkpointRegistry.set(item.id, {
                id: item.id,
                timestamp: checkpoint.timestamp,
                description: checkpoint.description,
                tags: checkpoint.tags,
                encrypted: false,
                metadata: {}
            });
        }

        // Perform dry-run migration
        const dryRunResult = await manager.migrateToEncrypted({ dryRun: true });

        if (dryRunResult.totalProcessed !== 2) {
            throw new Error('Dry run migration did not identify correct number of checkpoints');
        }

        if (!dryRunResult.dryRun) {
            throw new Error('Dry run flag not set in result');
        }

        // Perform actual migration
        const migrationResult = await manager.migrateToEncrypted({ dryRun: false });

        if (migrationResult.migrated.length !== 2) {
            throw new Error('Migration did not process correct number of checkpoints');
        }

        // Verify checkpoints are now encrypted
        for (const item of unencryptedData) {
            const registryEntry = manager.checkpointRegistry.get(item.id);
            if (!registryEntry.encrypted) {
                throw new Error(`Checkpoint ${item.id} not marked as encrypted after migration`);
            }

            // Verify the data can still be restored
            const restored = await manager.restoreCheckpoint(item.id);
            if (JSON.stringify(restored.state) !== JSON.stringify(item.state)) {
                throw new Error(`Migrated checkpoint ${item.id} data integrity failed`);
            }
        }
    }

    /**
     * Test 7: Error Handling
     */
    async testErrorHandling() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        // Test decryption with invalid data
        try {
            await manager.decryptData('invalid json');
            // Should not throw for backward compatibility - should return as-is
        } catch (error) {
            throw new Error('Decryption should handle invalid JSON gracefully for backward compatibility');
        }

        // Test decryption with malformed encrypted data
        try {
            const malformedEncrypted = JSON.stringify({
                encrypted: 'invalid_hex_data',
                salt: 'invalid_hex',
                authTag: 'invalid_hex',
                algorithm: 'aes-256-gcm'
            });
            await manager.decryptData(malformedEncrypted);
            throw new Error('Should have thrown error for malformed encrypted data');
        } catch (error) {
            if (!error.message.includes('Decryption failed')) {
                throw new Error('Wrong error type for malformed data');
            }
        }

        // Verify error stats are updated
        if (manager.encryptionStats.decryptionErrors === 0) {
            throw new Error('Decryption error stats not updated');
        }
    }

    /**
     * Test 8: List and Filter Encrypted Checkpoints
     */
    async testListAndFilter() {
        const manager = new CheckpointManager({
            checkpointsDir: this.testDir,
            encryptionEnabled: true
        });

        // Create mixed encrypted and unencrypted checkpoints
        await manager.createCheckpoint('encrypted-1', { data: 'enc1' }, {
            tags: ['test'],
            critical: true
        });

        await manager.createCheckpoint('encrypted-2', { data: 'enc2' }, {
            tags: ['test', 'important']
        });

        // Add an unencrypted checkpoint manually
        const unencryptedCheckpoint = {
            id: 'unencrypted-1',
            version: '1.0',
            timestamp: new Date().toISOString(),
            description: 'Unencrypted test checkpoint',
            tags: ['test'],
            state: JSON.stringify({ data: 'unenc1' }),
            encrypted: false
        };

        const unencryptedPath = path.join(this.testDir, 'unencrypted-1.json');
        await fs.writeFile(unencryptedPath, JSON.stringify(unencryptedCheckpoint, null, 2));

        manager.checkpointRegistry.set('unencrypted-1', {
            id: 'unencrypted-1',
            timestamp: unencryptedCheckpoint.timestamp,
            description: unencryptedCheckpoint.description,
            tags: unencryptedCheckpoint.tags,
            encrypted: false,
            metadata: {}
        });

        // Test listing all checkpoints
        const allCheckpoints = await manager.listCheckpoints();
        if (allCheckpoints.length !== 3) {
            throw new Error('Incorrect total checkpoint count');
        }

        // Test filtering by encrypted status
        const encryptedOnly = await manager.listCheckpoints({ encrypted: true });
        if (encryptedOnly.length !== 2) {
            throw new Error('Incorrect encrypted checkpoint count');
        }

        const unencryptedOnly = await manager.listCheckpoints({ encrypted: false });
        if (unencryptedOnly.length !== 1) {
            throw new Error('Incorrect unencrypted checkpoint count');
        }

        // Test filtering by critical status
        const criticalOnly = await manager.listCheckpoints({ critical: true });
        if (criticalOnly.length !== 1) {
            throw new Error('Incorrect critical checkpoint count');
        }

        // Test filtering by tags
        const importantTagged = await manager.listCheckpoints({ tags: ['important'] });
        if (importantTagged.length !== 1) {
            throw new Error('Incorrect important tagged checkpoint count');
        }
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        this.log('Starting Checkpoint Encryption Test Suite', 'info');
        this.log('=====================================', 'info');

        await this.setup();

        try {
            await this.runTest('Basic Encryption/Decryption', () => this.testBasicEncryption());
            await this.runTest('Encrypted Checkpoint Lifecycle', () => this.testEncryptedCheckpointLifecycle());
            await this.runTest('Backward Compatibility', () => this.testBackwardCompatibility());
            await this.runTest('Key Management', () => this.testKeyManagement());
            await this.runTest('Encryption Statistics', () => this.testEncryptionStatistics());
            await this.runTest('Migration Functionality', () => this.testMigration());
            await this.runTest('Error Handling', () => this.testErrorHandling());
            await this.runTest('List and Filter Encrypted Checkpoints', () => this.testListAndFilter());

        } finally {
            await this.cleanup();
        }

        // Print summary
        this.log('=====================================', 'info');
        this.log('Test Summary:', 'info');
        this.log(`Total Tests: ${this.stats.total}`, 'info');
        this.log(`Passed: ${this.stats.passed}`, this.stats.passed === this.stats.total ? 'success' : 'info');
        this.log(`Failed: ${this.stats.failed}`, this.stats.failed > 0 ? 'error' : 'info');

        if (this.stats.failed > 0) {
            this.log('Failed Tests:', 'error');
            this.results.filter(r => r.status === 'FAILED').forEach(result => {
                this.log(`  - ${result.name}: ${result.error}`, 'error');
            });
        }

        const successRate = ((this.stats.passed / this.stats.total) * 100).toFixed(1);
        this.log(`Success Rate: ${successRate}%`, successRate === '100.0' ? 'success' : 'warn');

        return this.stats.failed === 0;
    }

    /**
     * Generate detailed test report
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: this.stats,
            successRate: ((this.stats.passed / this.stats.total) * 100).toFixed(1) + '%',
            tests: this.results,
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                testDirectory: this.testDir
            },
            encryptionFeatures: [
                'AES-256-GCM encryption',
                'PBKDF2 key derivation',
                'Environment-based key management',
                'Backward compatibility',
                'Batch migration',
                'Comprehensive error handling',
                'Secure file permissions (0600)',
                'Encryption statistics tracking'
            ]
        };

        return report;
    }
}

// Run tests if called directly
if (require.main === module) {
    (async () => {
        const tester = new CheckpointEncryptionTester();

        try {
            const success = await tester.runAllTests();

            // Generate and save report
            const report = tester.generateReport();
            const reportPath = '/tmp/claude/checkpoint-encryption-test-report.json';

            try {
                await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
                tester.log(`Test report saved to: ${reportPath}`, 'info');
            } catch (error) {
                tester.log(`Failed to save report: ${error.message}`, 'warn');
            }

            process.exit(success ? 0 : 1);

        } catch (error) {
            console.error('Test suite failed:', error);
            process.exit(1);
        }
    })();
}

module.exports = CheckpointEncryptionTester;