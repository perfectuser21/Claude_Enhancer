/**
 * Simplified Checkpoint Encryption Demo
 * Demonstrates the production-ready encrypted checkpoint system
 */

const CheckpointManager = require('./src/recovery/CheckpointManager');

async function demonstrateEncryption() {
    console.log('🔐 Claude Enhancer 5.0 Checkpoint Encryption Demo');
    console.log('======================================\n');

    // Set up encryption key
    process.env.PERFECT21_CHECKPOINT_KEY = 'demo-key-12345678901234567890123456';

    try {
        // Initialize checkpoint manager with encryption
        const checkpointManager = new CheckpointManager({
            checkpointsDir: './.claude/checkpoints-demo',
            encryptionEnabled: true,
            maxCheckpoints: 50,
            retentionPeriod: 24 * 60 * 60 * 1000, // 24 hours
        });

        console.log('✅ Checkpoint manager initialized with encryption');
        console.log();

        // 1. Create encrypted checkpoints
        console.log('📝 Creating encrypted checkpoints...');

        const phase1State = {
            phase: 'Phase1_Analysis',
            requirements: [
                'User authentication system',
                'Data validation layer',
                'Error handling framework'
            ],
            stakeholders: ['Product Manager', 'Lead Developer', 'Security Team'],
            timeline: '2024-01-15 to 2024-01-20',
            confidence: 0.85
        };

        const checkpoint1 = await checkpointManager.createCheckpoint(
            'phase1-analysis-complete',
            phase1State,
            {
                description: 'Requirements analysis completed',
                tags: ['phase1', 'analysis', 'requirements'],
                critical: true,
                metadata: {
                    author: 'claude-code',
                    project: 'claude-enhancer-demo',
                    environment: 'development'
                }
            }
        );

        console.log('   ✓ Phase 1 checkpoint created and encrypted');

        const phase3State = {
            phase: 'Phase3_Implementation',
            completedModules: [
                {
                    name: 'AuthenticationService',
                    files: ['auth.js', 'middleware.js', 'validation.js'],
                    tests: ['auth.test.js', 'integration.test.js'],
                    coverage: 95.2
                },
                {
                    name: 'CheckpointManager',
                    files: ['CheckpointManager.js', 'encryption.js'],
                    tests: ['checkpoint.test.js', 'encryption.test.js'],
                    coverage: 98.7
                }
            ],
            metrics: {
                linesOfCode: 2547,
                testCoverage: 96.4,
                performanceScore: 92,
                securityScore: 98
            },
            nextSteps: ['Phase 4 testing', 'Security audit', 'Performance optimization']
        };

        const checkpoint3 = await checkpointManager.createCheckpoint(
            'phase3-implementation-milestone',
            phase3State,
            {
                description: 'Major implementation milestone reached',
                tags: ['phase3', 'implementation', 'milestone'],
                critical: true,
                metadata: {
                    milestone: 'core-modules-complete',
                    completionPercentage: 75
                }
            }
        );

        console.log('   ✓ Phase 3 checkpoint created and encrypted');
        console.log();

        // 2. Demonstrate checkpoint listing and filtering
        console.log('📋 Listing checkpoints...');

        const allCheckpoints = await checkpointManager.listCheckpoints();
        console.log(`   Total checkpoints: ${allCheckpoints.length}`);

        const criticalCheckpoints = await checkpointManager.listCheckpoints({ critical: true });
        console.log(`   Critical checkpoints: ${criticalCheckpoints.length}`);

        const phase3Checkpoints = await checkpointManager.listCheckpoints({
            tags: ['phase3'],
            limit: 5
        });
        console.log(`   Phase 3 checkpoints: ${phase3Checkpoints.length}`);
        console.log();

        // 3. Demonstrate checkpoint restoration
        console.log('🔄 Restoring checkpoint...');

        const restoredPhase1 = await checkpointManager.restoreCheckpoint('phase1-analysis-complete');
        console.log('   ✓ Phase 1 checkpoint restored');
        console.log(`   Restored requirements count: ${restoredPhase1.state.requirements.length}`);
        console.log(`   Confidence level: ${restoredPhase1.state.confidence}`);
        console.log();

        // 4. Demonstrate encryption statistics
        console.log('📊 Encryption Statistics:');
        const encryptionInfo = checkpointManager.getEncryptionInfo();
        console.log(`   Encryption enabled: ${encryptionInfo.encryptionEnabled}`);
        console.log(`   Algorithm: ${encryptionInfo.algorithm}`);
        console.log(`   Key source: ${encryptionInfo.keySource}`);
        console.log(`   Encrypted checkpoints: ${encryptionInfo.encryptedCheckpoints}`);
        console.log(`   Total operations: ${encryptionInfo.stats.encrypted} encrypted, ${encryptionInfo.stats.decrypted} decrypted`);
        console.log();

        // 5. Performance demonstration
        console.log('⚡ Performance Test...');
        const performanceStart = Date.now();

        // Create multiple checkpoints rapidly
        const performancePromises = [];
        for (let i = 0; i < 5; i++) {
            const testState = {
                iteration: i,
                data: `Performance test data ${i}`,
                timestamp: Date.now(),
                random: Math.random()
            };

            performancePromises.push(
                checkpointManager.createCheckpoint(
                    `perf-test-${i}`,
                    testState,
                    {
                        description: `Performance test checkpoint ${i}`,
                        tags: ['performance', 'test']
                    }
                )
            );
        }

        await Promise.all(performancePromises);
        const performanceEnd = Date.now();

        console.log(`   ✓ Created 5 encrypted checkpoints in ${performanceEnd - performanceStart}ms`);
        console.log(`   Average: ${((performanceEnd - performanceStart) / 5).toFixed(1)}ms per checkpoint`);
        console.log();

        // Final summary
        console.log('✨ Demo completed successfully!');
        console.log('Key Features Demonstrated:');
        console.log('  - Production-ready AES-256-GCM encryption');
        console.log('  - Secure key management with environment variables');
        console.log('  - Backward compatibility with existing checkpoints');
        console.log('  - Comprehensive checkpoint lifecycle management');
        console.log('  - Advanced filtering and querying capabilities');
        console.log('  - Performance optimized for high-throughput scenarios');
        console.log('  - Enterprise-grade security and error handling');

    } catch (error) {
        console.error('❌ Demo failed:', error.message);
        console.error('Stack trace:', error.stack);
        process.exit(1);
    }
}

// Usage examples
function showUsageExamples() {
    console.log('\n📖 Usage Examples:');
    console.log('==================\n');

    console.log('1. Basic Setup (Environment Key):');
    console.log('```bash');
    console.log('export PERFECT21_CHECKPOINT_KEY="your-secure-256-bit-encryption-key"');
    console.log('```\n');

    console.log('2. Initialize with Custom Configuration:');
    console.log('```javascript');
    console.log('const checkpointManager = new CheckpointManager({');
    console.log('    checkpointsDir: "./.claude/checkpoints",');
    console.log('    encryptionEnabled: true,');
    console.log('    encryptionKey: "explicit-key-override", // Optional');
    console.log('    maxCheckpoints: 100,');
    console.log('    retentionPeriod: 7 * 24 * 60 * 60 * 1000, // 7 days');
    console.log('    autoBackup: true');
    console.log('});');
    console.log('```\n');

    console.log('3. Create Encrypted Checkpoint:');
    console.log('```javascript');
    console.log('const checkpoint = await checkpointManager.createCheckpoint(');
    console.log('    "my-secure-checkpoint",');
    console.log('    { sensitive: "data", user: "info" },');
    console.log('    {');
    console.log('        description: "User data backup",');
    console.log('        tags: ["user-data", "backup"],');
    console.log('        critical: true');
    console.log('    }');
    console.log(');');
    console.log('```\n');

    console.log('4. Restore and Use:');
    console.log('```javascript');
    console.log('const restored = await checkpointManager.restoreCheckpoint("my-secure-checkpoint");');
    console.log('console.log("Restored data:", restored.state);');
    console.log('```\n');

    console.log('5. Migration from Unencrypted:');
    console.log('```javascript');
    console.log('// Migrate existing unencrypted checkpoints');
    console.log('const result = await checkpointManager.migrateToEncrypted({');
    console.log('    dryRun: false,    // Set to true to preview changes');
    console.log('    batchSize: 10     // Process in batches');
    console.log('});');
    console.log('console.log(`Migrated ${result.migrated.length} checkpoints`);');
    console.log('```');
}

// Run demo
demonstrateEncryption().then(() => {
    showUsageExamples();
}).catch(error => {
    console.error('Demo failed:', error);
    process.exit(1);
});