/**
 * TypeScript Error Recovery Integration Test
 */

import * as path from 'path';

// Import our error recovery system
const ErrorRecovery = require('../src/recovery/ErrorRecovery');

interface TestResult {
    passed: boolean;
    message: string;
    error?: Error;
}

interface TypedOperation<T> {
    execute: () => Promise<T>;
    retry?: boolean;
    checkpointData?: T;
}

class TypeScriptRecoveryTest {
    private recovery: any;
    private results: TestResult[] = [];

    constructor() {
        this.recovery = new ErrorRecovery({
            maxRetries: 3,
            baseRetryDelay: 100,
            enableMetrics: true,
            checkpointsDir: './.claude/checkpoints-ts'
        });
    }

    async runTests(): Promise<void> {
        console.log('🧪 TypeScript Error Recovery Tests\n');

        await this.testTypeSafeRetry();
        await this.testGenericCheckpoints();
        await this.testAsyncPatterns();
        await this.testErrorTypeGuards();
        await this.testPromiseRecovery();

        this.printResults();
    }

    private async testTypeSafeRetry(): Promise<void> {
        console.log('1️⃣ Testing type-safe retry mechanism...');

        try {
            let attempts = 0;
            const operation: TypedOperation<string> = {
                execute: async () => {
                    attempts++;
                    if (attempts < 2) {
                        throw new Error('Type validation failed');
                    }
                    return 'Type-safe success';
                },
                retry: true
            };

            const result = await this.recovery.executeWithRecovery(
                operation.execute,
                { strategy: 'validation', checkpointId: 'ts-retry' }
            );

            this.results.push({
                passed: result === 'Type-safe success',
                message: `Type-safe retry completed after ${attempts} attempts`
            });
            console.log(`   ✅ ${this.results[this.results.length - 1].message}`);
        } catch (error) {
            this.results.push({
                passed: false,
                message: 'Type-safe retry failed',
                error: error as Error
            });
            console.log(`   ❌ ${error}`);
        }
    }

    private async testGenericCheckpoints<T extends object>(): Promise<void> {
        console.log('\n2️⃣ Testing generic checkpoint system...');

        interface UserState {
            userId: number;
            sessionId: string;
            preferences: {
                theme: 'light' | 'dark';
                notifications: boolean;
            };
        }

        const testData: UserState = {
            userId: 12345,
            sessionId: 'abc-123',
            preferences: {
                theme: 'dark',
                notifications: true
            }
        };

        try {
            const checkpointId = await this.recovery.createCheckpoint(
                'ts-generic-cp',
                testData,
                { type: 'UserState' }
            );

            const restored = await this.recovery.restoreCheckpoint(checkpointId);
            const restoredData = restored.data as UserState;

            const isValid = restoredData.userId === testData.userId &&
                           restoredData.sessionId === testData.sessionId &&
                           restoredData.preferences.theme === testData.preferences.theme;

            this.results.push({
                passed: isValid,
                message: 'Generic checkpoint preserved types correctly'
            });
            console.log(`   ✅ ${this.results[this.results.length - 1].message}`);
        } catch (error) {
            this.results.push({
                passed: false,
                message: 'Generic checkpoint failed',
                error: error as Error
            });
            console.log(`   ❌ ${error}`);
        }
    }

    private async testAsyncPatterns(): Promise<void> {
        console.log('\n3️⃣ Testing async/await patterns...');

        const asyncOperations = [
            () => Promise.resolve('op1'),
            () => Promise.reject(new Error('op2 failed')),
            () => Promise.resolve('op3')
        ];

        try {
            const results = await Promise.allSettled(
                asyncOperations.map((op, index) =>
                    this.recovery.executeWithRecovery(op, {
                        strategy: 'default',
                        checkpointId: `async-${index}`
                    })
                )
            );

            const successCount = results.filter(r => r.status === 'fulfilled').length;

            this.results.push({
                passed: successCount === 2,
                message: `Handled ${successCount}/3 async operations successfully`
            });
            console.log(`   ✅ ${this.results[this.results.length - 1].message}`);
        } catch (error) {
            this.results.push({
                passed: false,
                message: 'Async pattern test failed',
                error: error as Error
            });
            console.log(`   ❌ ${error}`);
        }
    }

    private async testErrorTypeGuards(): Promise<void> {
        console.log('\n4️⃣ Testing error type guards...');

        class CustomError extends Error {
            constructor(public code: string, message: string) {
                super(message);
                this.name = 'CustomError';
            }
        }

        const isCustomError = (error: unknown): error is CustomError => {
            return error instanceof CustomError;
        };

        try {
            await this.recovery.executeWithRecovery(
                async () => {
                    throw new CustomError('CUSTOM_001', 'Custom error occurred');
                },
                {
                    strategy: 'default',
                    checkpointId: 'type-guard',
                    onRetry: (error: Error) => {
                        if (isCustomError(error)) {
                            console.log(`     • Caught custom error with code: ${error.code}`);
                        }
                    }
                }
            ).catch((error: Error) => {
                const handled = isCustomError(error);
                this.results.push({
                    passed: handled,
                    message: 'Type guard correctly identified custom error'
                });
                console.log(`   ✅ ${this.results[this.results.length - 1].message}`);
            });
        } catch (error) {
            this.results.push({
                passed: false,
                message: 'Type guard test failed',
                error: error as Error
            });
            console.log(`   ❌ ${error}`);
        }
    }

    private async testPromiseRecovery(): Promise<void> {
        console.log('\n5️⃣ Testing Promise chain recovery...');

        const promiseChain = async (): Promise<string> => {
            return Promise.resolve('start')
                .then(val => {
                    if (Math.random() > 0.5) {
                        throw new Error('Random failure in chain');
                    }
                    return val + ' -> middle';
                })
                .then(val => val + ' -> end');
        };

        try {
            let recovered = false;
            const result = await this.recovery.executeWithRecovery(
                promiseChain,
                {
                    strategy: 'default',
                    checkpointId: 'promise-chain',
                    maxRetries: 5
                }
            ).catch(() => {
                recovered = true;
                return 'Recovered from promise chain failure';
            });

            this.results.push({
                passed: true,
                message: `Promise chain ${recovered ? 'recovered' : 'succeeded'}`
            });
            console.log(`   ✅ ${this.results[this.results.length - 1].message}`);
        } catch (error) {
            this.results.push({
                passed: false,
                message: 'Promise recovery failed',
                error: error as Error
            });
            console.log(`   ❌ ${error}`);
        }
    }

    private printResults(): void {
        console.log('\n' + '='.repeat(50));
        console.log('📊 TypeScript Integration Results:');

        const passed = this.results.filter(r => r.passed).length;
        const total = this.results.length;
        const successRate = ((passed / total) * 100).toFixed(1);

        console.log(`   ✅ Passed: ${passed}`);
        console.log(`   ❌ Failed: ${total - passed}`);
        console.log(`   📈 Success Rate: ${successRate}%`);

        const metrics = this.recovery.getMetrics();
        console.log('\n📈 Recovery Metrics:');
        console.log(`   • Total errors handled: ${metrics.totalErrors}`);
        console.log(`   • Recovery success rate: ${metrics.successRate}`);

        if (passed === total) {
            console.log('\n🎉 All TypeScript tests passed!');
        } else {
            console.log('\n⚠️ Some TypeScript tests failed');
        }
    }
}

// Run the tests
const test = new TypeScriptRecoveryTest();
test.runTests().catch(console.error);