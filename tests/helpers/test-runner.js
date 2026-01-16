/**
 * Simple Test Runner for E2E Tests
 * Provides describe/it/expect functionality without external dependencies
 */

class TestRunner {
    constructor() {
        this.tests = [];
        this.currentSuite = null;
        this.results = { passed: 0, failed: 0, errors: [] };
        this.globalBeforeAll = null;
        this.globalAfterAll = null;
    }

    describe(name, fn) {
        const suite = { name, tests: [], beforeEach: null, afterEach: null };
        const prevSuite = this.currentSuite;
        this.currentSuite = suite;
        fn();
        this.currentSuite = prevSuite;
        if (prevSuite) {
            prevSuite.tests.push(suite);
        } else {
            this.tests.push(suite);
        }
    }

    it(name, fn) {
        if (!this.currentSuite) {
            throw new Error('it() called outside describe()');
        }
        this.currentSuite.tests.push({ name, fn, type: 'test' });
    }

    beforeEach(fn) {
        if (!this.currentSuite) {
            throw new Error('beforeEach() called outside describe()');
        }
        this.currentSuite.beforeEach = fn;
    }

    afterEach(fn) {
        if (!this.currentSuite) {
            throw new Error('afterEach() called outside describe()');
        }
        this.currentSuite.afterEach = fn;
    }

    beforeAll(fn) {
        if (!this.currentSuite) {
            throw new Error('beforeAll() called outside describe()');
        }
        this.currentSuite.beforeAll = fn;
    }

    afterAll(fn) {
        if (!this.currentSuite) {
            throw new Error('afterAll() called outside describe()');
        }
        this.currentSuite.afterAll = fn;
    }

    async run() {
        console.log('\nRunning tests...\n');
        if (this.globalBeforeAll) {
            await this.globalBeforeAll();
        }
        await this.runSuite(this.tests, '');
        if (this.globalAfterAll) {
            await this.globalAfterAll();
        }
        this.printResults();
        return this.results.failed === 0 ? 0 : 1;
    }
    
    setGlobalBeforeAll(fn) {
        this.globalBeforeAll = fn;
    }
    
    setGlobalAfterAll(fn) {
        this.globalAfterAll = fn;
    }

    async runSuite(suites, indent) {
        for (const suite of suites) {
            if (suite.type === 'test') {
                await this.runTest(suite, indent);
            } else {
                console.log(`${indent}${suite.name}`);
                if (suite.beforeAll) {
                    await suite.beforeAll();
                }
                await this.runSuite(suite.tests, indent + '  ');
                if (suite.afterAll) {
                    await suite.afterAll();
                }
            }
        }
    }

    async runTest(test, indent) {
        try {
            const suite = this.findSuite(test);
            if (suite && suite.beforeEach) {
                await suite.beforeEach();
            }

            await test.fn();

            if (suite && suite.afterEach) {
                await suite.afterEach();
            }

            console.log(`${indent}✓ ${test.name}`);
            this.results.passed++;
        } catch (error) {
            console.log(`${indent}✗ ${test.name}`);
            console.log(`${indent}  ${error.message}`);
            this.results.failed++;
            this.results.errors.push({ test: test.name, error: error.message });
        }
    }

    findSuite(test) {
        for (const suite of this.tests) {
            if (this.findInSuite(suite, test)) {
                return suite;
            }
        }
        return null;
    }

    findInSuite(suite, test) {
        if (suite.tests.includes(test)) {
            return suite;
        }
        for (const item of suite.tests) {
            if (item.tests && this.findInSuite(item, test)) {
                return suite;
            }
        }
        return null;
    }

    printResults() {
        console.log('\n' + '='.repeat(50));
        console.log(`Tests: ${this.results.passed} passed, ${this.results.failed} failed`);
        if (this.results.errors.length > 0) {
            console.log('\nErrors:');
            this.results.errors.forEach(({ test, error }) => {
                console.log(`  ${test}: ${error}`);
            });
        }
        console.log('='.repeat(50) + '\n');
    }
}

// Expect matcher
class Expect {
    constructor(value) {
        this.value = value;
    }

    toBe(expected) {
        if (this.value !== expected) {
            throw new Error(`Expected ${this.value} to be ${expected}`);
        }
    }

    toEqual(expected) {
        if (JSON.stringify(this.value) !== JSON.stringify(expected)) {
            throw new Error(`Expected ${JSON.stringify(this.value)} to equal ${JSON.stringify(expected)}`);
        }
    }

    toHaveProperty(prop) {
        if (!(prop in this.value)) {
            throw new Error(`Expected object to have property ${prop}`);
        }
    }

    toBeDefined() {
        if (this.value === undefined) {
            throw new Error('Expected value to be defined');
        }
    }

    toBeTruthy() {
        if (!this.value) {
            throw new Error('Expected value to be truthy');
        }
    }

    toBeInstanceOf(type) {
        if (!(this.value instanceof type)) {
            throw new Error(`Expected ${this.value} to be instance of ${type.name}`);
        }
    }

    toContain(item) {
        if (Array.isArray(this.value)) {
            if (!this.value.includes(item)) {
                throw new Error(`Expected array to contain ${item}`);
            }
        } else if (typeof this.value === 'string') {
            if (!this.value.includes(item)) {
                throw new Error(`Expected string to contain ${item}`);
            }
        } else {
            throw new Error('toContain can only be used with arrays or strings');
        }
    }

    toBeGreaterThan(expected) {
        if (this.value <= expected) {
            throw new Error(`Expected ${this.value} to be greater than ${expected}`);
        }
    }

    toBeLessThan(expected) {
        if (this.value >= expected) {
            throw new Error(`Expected ${this.value} to be less than ${expected}`);
        }
    }

    toBeGreaterThanOrEqual(expected) {
        if (this.value < expected) {
            throw new Error(`Expected ${this.value} to be greater than or equal to ${expected}`);
        }
    }

    not = {
        toBe: (expected) => {
            if (this.value === expected) {
                throw new Error(`Expected ${this.value} not to be ${expected}`);
            }
        },
        toContain: (item) => {
            if (Array.isArray(this.value)) {
                if (this.value.includes(item)) {
                    throw new Error(`Expected array not to contain ${item}`);
                }
            } else if (typeof this.value === 'string') {
                if (this.value.includes(item)) {
                    throw new Error(`Expected string not to contain ${item}`);
                }
            }
        },
        toBeDefined: () => {
            if (this.value !== undefined) {
                throw new Error('Expected value not to be defined');
            }
        },
    };
}

function expect(value) {
    return new Expect(value);
}

// Create singleton instance
const runner = new TestRunner();

// Export for use in test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        describe: runner.describe.bind(runner),
        it: runner.it.bind(runner),
        beforeEach: runner.beforeEach.bind(runner),
        afterEach: runner.afterEach.bind(runner),
        beforeAll: runner.beforeAll.bind(runner),
        afterAll: runner.afterAll.bind(runner),
        setGlobalBeforeAll: runner.setGlobalBeforeAll.bind(runner),
        setGlobalAfterAll: runner.setGlobalAfterAll.bind(runner),
        expect,
        run: () => runner.run(),
    };
}
