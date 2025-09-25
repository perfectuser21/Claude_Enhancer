"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkMemoryLimit = checkMemoryLimit;
var config = {
    maxMemory: 1024,
    enabled: true
};
function checkMemoryLimit() {
    console.log('TypeScript service memory limit:', config.maxMemory, 'MB');
    return config.enabled;
}
// This file helps trigger TypeScript language service
checkMemoryLimit();
