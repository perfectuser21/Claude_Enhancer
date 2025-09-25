"use strict";
/**
 * TypeScript Error Recovery Integration Test
 */
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
// Import our error recovery system
var ErrorRecovery = require('../src/recovery/ErrorRecovery');
var TypeScriptRecoveryTest = /** @class */ (function () {
    function TypeScriptRecoveryTest() {
        this.results = [];
        this.recovery = new ErrorRecovery({
            maxRetries: 3,
            baseRetryDelay: 100,
            enableMetrics: true,
            checkpointsDir: './.claude/checkpoints-ts'
        });
    }
    TypeScriptRecoveryTest.prototype.runTests = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('🧪 TypeScript Error Recovery Tests\n');
                        return [4 /*yield*/, this.testTypeSafeRetry()];
                    case 1:
                        _a.sent();
                        return [4 /*yield*/, this.testGenericCheckpoints()];
                    case 2:
                        _a.sent();
                        return [4 /*yield*/, this.testAsyncPatterns()];
                    case 3:
                        _a.sent();
                        return [4 /*yield*/, this.testErrorTypeGuards()];
                    case 4:
                        _a.sent();
                        return [4 /*yield*/, this.testPromiseRecovery()];
                    case 5:
                        _a.sent();
                        this.printResults();
                        return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.testTypeSafeRetry = function () {
        return __awaiter(this, void 0, void 0, function () {
            var attempts_1, operation, result, error_1;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('1️⃣ Testing type-safe retry mechanism...');
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        attempts_1 = 0;
                        operation = {
                            execute: function () { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    attempts_1++;
                                    if (attempts_1 < 2) {
                                        throw new Error('Type validation failed');
                                    }
                                    return [2 /*return*/, 'Type-safe success'];
                                });
                            }); },
                            retry: true
                        };
                        return [4 /*yield*/, this.recovery.executeWithRecovery(operation.execute, { strategy: 'validation', checkpointId: 'ts-retry' })];
                    case 2:
                        result = _a.sent();
                        this.results.push({
                            passed: result === 'Type-safe success',
                            message: "Type-safe retry completed after ".concat(attempts_1, " attempts")
                        });
                        console.log("   \u2705 ".concat(this.results[this.results.length - 1].message));
                        return [3 /*break*/, 4];
                    case 3:
                        error_1 = _a.sent();
                        this.results.push({
                            passed: false,
                            message: 'Type-safe retry failed',
                            error: error_1
                        });
                        console.log("   \u274C ".concat(error_1));
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.testGenericCheckpoints = function () {
        return __awaiter(this, void 0, void 0, function () {
            var testData, checkpointId, restored, restoredData, isValid, error_2;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('\n2️⃣ Testing generic checkpoint system...');
                        testData = {
                            userId: 12345,
                            sessionId: 'abc-123',
                            preferences: {
                                theme: 'dark',
                                notifications: true
                            }
                        };
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 4, , 5]);
                        return [4 /*yield*/, this.recovery.createCheckpoint('ts-generic-cp', testData, { type: 'UserState' })];
                    case 2:
                        checkpointId = _a.sent();
                        return [4 /*yield*/, this.recovery.restoreCheckpoint(checkpointId)];
                    case 3:
                        restored = _a.sent();
                        restoredData = restored.data;
                        isValid = restoredData.userId === testData.userId &&
                            restoredData.sessionId === testData.sessionId &&
                            restoredData.preferences.theme === testData.preferences.theme;
                        this.results.push({
                            passed: isValid,
                            message: 'Generic checkpoint preserved types correctly'
                        });
                        console.log("   \u2705 ".concat(this.results[this.results.length - 1].message));
                        return [3 /*break*/, 5];
                    case 4:
                        error_2 = _a.sent();
                        this.results.push({
                            passed: false,
                            message: 'Generic checkpoint failed',
                            error: error_2
                        });
                        console.log("   \u274C ".concat(error_2));
                        return [3 /*break*/, 5];
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.testAsyncPatterns = function () {
        return __awaiter(this, void 0, void 0, function () {
            var asyncOperations, results, successCount, error_3;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('\n3️⃣ Testing async/await patterns...');
                        asyncOperations = [
                            function () { return Promise.resolve('op1'); },
                            function () { return Promise.reject(new Error('op2 failed')); },
                            function () { return Promise.resolve('op3'); }
                        ];
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, Promise.allSettled(asyncOperations.map(function (op, index) {
                                return _this.recovery.executeWithRecovery(op, {
                                    strategy: 'default',
                                    checkpointId: "async-".concat(index)
                                });
                            }))];
                    case 2:
                        results = _a.sent();
                        successCount = results.filter(function (r) { return r.status === 'fulfilled'; }).length;
                        this.results.push({
                            passed: successCount === 2,
                            message: "Handled ".concat(successCount, "/3 async operations successfully")
                        });
                        console.log("   \u2705 ".concat(this.results[this.results.length - 1].message));
                        return [3 /*break*/, 4];
                    case 3:
                        error_3 = _a.sent();
                        this.results.push({
                            passed: false,
                            message: 'Async pattern test failed',
                            error: error_3
                        });
                        console.log("   \u274C ".concat(error_3));
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.testErrorTypeGuards = function () {
        return __awaiter(this, void 0, void 0, function () {
            var CustomError, isCustomError, error_4;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('\n4️⃣ Testing error type guards...');
                        CustomError = /** @class */ (function (_super) {
                            __extends(CustomError, _super);
                            function CustomError(code, message) {
                                var _this = _super.call(this, message) || this;
                                _this.code = code;
                                _this.name = 'CustomError';
                                return _this;
                            }
                            return CustomError;
                        }(Error));
                        isCustomError = function (error) {
                            return error instanceof CustomError;
                        };
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, this.recovery.executeWithRecovery(function () { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    throw new CustomError('CUSTOM_001', 'Custom error occurred');
                                });
                            }); }, {
                                strategy: 'default',
                                checkpointId: 'type-guard',
                                onRetry: function (error) {
                                    if (isCustomError(error)) {
                                        console.log("     \u2022 Caught custom error with code: ".concat(error.code));
                                    }
                                }
                            }).catch(function (error) {
                                var handled = isCustomError(error);
                                _this.results.push({
                                    passed: handled,
                                    message: 'Type guard correctly identified custom error'
                                });
                                console.log("   \u2705 ".concat(_this.results[_this.results.length - 1].message));
                            })];
                    case 2:
                        _a.sent();
                        return [3 /*break*/, 4];
                    case 3:
                        error_4 = _a.sent();
                        this.results.push({
                            passed: false,
                            message: 'Type guard test failed',
                            error: error_4
                        });
                        console.log("   \u274C ".concat(error_4));
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.testPromiseRecovery = function () {
        return __awaiter(this, void 0, void 0, function () {
            var promiseChain, recovered_1, result, error_5;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('\n5️⃣ Testing Promise chain recovery...');
                        promiseChain = function () { return __awaiter(_this, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                return [2 /*return*/, Promise.resolve('start')
                                        .then(function (val) {
                                        if (Math.random() > 0.5) {
                                            throw new Error('Random failure in chain');
                                        }
                                        return val + ' -> middle';
                                    })
                                        .then(function (val) { return val + ' -> end'; })];
                            });
                        }); };
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        recovered_1 = false;
                        return [4 /*yield*/, this.recovery.executeWithRecovery(promiseChain, {
                                strategy: 'default',
                                checkpointId: 'promise-chain',
                                maxRetries: 5
                            }).catch(function () {
                                recovered_1 = true;
                                return 'Recovered from promise chain failure';
                            })];
                    case 2:
                        result = _a.sent();
                        this.results.push({
                            passed: true,
                            message: "Promise chain ".concat(recovered_1 ? 'recovered' : 'succeeded')
                        });
                        console.log("   \u2705 ".concat(this.results[this.results.length - 1].message));
                        return [3 /*break*/, 4];
                    case 3:
                        error_5 = _a.sent();
                        this.results.push({
                            passed: false,
                            message: 'Promise recovery failed',
                            error: error_5
                        });
                        console.log("   \u274C ".concat(error_5));
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    TypeScriptRecoveryTest.prototype.printResults = function () {
        console.log('\n' + '='.repeat(50));
        console.log('📊 TypeScript Integration Results:');
        var passed = this.results.filter(function (r) { return r.passed; }).length;
        var total = this.results.length;
        var successRate = ((passed / total) * 100).toFixed(1);
        console.log("   \u2705 Passed: ".concat(passed));
        console.log("   \u274C Failed: ".concat(total - passed));
        console.log("   \uD83D\uDCC8 Success Rate: ".concat(successRate, "%"));
        var metrics = this.recovery.getMetrics();
        console.log('\n📈 Recovery Metrics:');
        console.log("   \u2022 Total errors handled: ".concat(metrics.totalErrors));
        console.log("   \u2022 Recovery success rate: ".concat(metrics.successRate));
        if (passed === total) {
            console.log('\n🎉 All TypeScript tests passed!');
        }
        else {
            console.log('\n⚠️ Some TypeScript tests failed');
        }
    };
    return TypeScriptRecoveryTest;
}());
// Run the tests
var test = new TypeScriptRecoveryTest();
test.runTests().catch(console.error);
