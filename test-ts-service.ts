// Test file to trigger TypeScript service
interface TestConfig {
    maxMemory: number;
    enabled: boolean;
}

const config: TestConfig = {
    maxMemory: 1024,
    enabled: true
};

export function checkMemoryLimit(): boolean {
    console.log('TypeScript service memory limit:', config.maxMemory, 'MB');
    return config.enabled;
}

// This file helps trigger TypeScript language service
checkMemoryLimit();