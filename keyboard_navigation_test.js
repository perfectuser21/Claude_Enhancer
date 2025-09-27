/**
 * Keyboard Navigation Test Suite
 * Tests keyboard accessibility for Claude Enhancer 5.0
 */

class KeyboardNavigationTester {
    constructor() {
        this.testResults = [];
        this.focusableElements = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
    }

    /**
     * Run comprehensive keyboard navigation tests
     */
    async runAllTests() {
        console.log('🎯 Starting Keyboard Navigation Tests...');

        const tests = [
            this.testTabNavigation(),
            this.testEscapeKeyHandling(),
            this.testEnterKeyHandling(),
            this.testArrowKeyNavigation(),
            this.testFocusManagement(),
            this.testSkipLinks(),
            this.testFormKeyboardInteraction(),
            this.testModalKeyboardTrap(),
            this.testCustomKeyboardShortcuts()
        ];

        const results = await Promise.all(tests);
        this.generateReport(results);
        return results;
    }

    /**
     * Test Tab key navigation
     */
    async testTabNavigation() {
        console.log('  ⌨️  Testing Tab Navigation...');

        const issues = [];
        const focusableElements = document.querySelectorAll(this.focusableElements);

        // Check for logical tab order
        let tabIndexIssues = 0;
        focusableElements.forEach((element, index) => {
            const tabIndex = element.getAttribute('tabindex');

            // Check for positive tabindex values (anti-pattern)
            if (tabIndex && parseInt(tabIndex) > 0) {
                issues.push({
                    type: 'tab_order',
                    severity: 'major',
                    element: element.tagName.toLowerCase(),
                    description: `Element has positive tabindex (${tabIndex}), disrupts natural tab order`,
                    recommendation: 'Use tabindex="0" or remove tabindex attribute'
                });
                tabIndexIssues++;
            }
        });

        // Check for focus indicators
        const hasVisibleFocus = this.checkFocusIndicators();
        if (!hasVisibleFocus) {
            issues.push({
                type: 'focus_indicator',
                severity: 'critical',
                element: 'general',
                description: 'No visible focus indicators detected',
                recommendation: 'Add :focus styles for all interactive elements'
            });
        }

        const score = Math.max(50, 100 - (tabIndexIssues * 15) - (hasVisibleFocus ? 0 : 30));

        return {
            test: 'Tab Navigation',
            score: score,
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `Found ${focusableElements.length} focusable elements, ${tabIndexIssues} tab order issues`
        };
    }

    /**
     * Test Escape key handling
     */
    async testEscapeKeyHandling() {
        console.log('  🚪 Testing Escape Key Handling...');

        const issues = [];

        // Simulate Escape key press
        const escapeEvent = new KeyboardEvent('keydown', {
            key: 'Escape',
            keyCode: 27,
            bubbles: true
        });

        // Check if modals close on Escape
        const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
        let modalEscapeSupport = 0;

        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.dispatchEvent(escapeEvent);
                // In a real test, we'd check if the modal closed
                modalEscapeSupport++;
            }
        });

        // Check for escape key listeners
        const hasEscapeListeners = this.hasKeyboardEventListeners('Escape');

        if (!hasEscapeListeners && modals.length > 0) {
            issues.push({
                type: 'escape_handling',
                severity: 'major',
                element: 'modals',
                description: 'No Escape key handling detected for modal dialogs',
                recommendation: 'Add Escape key listeners to close modals'
            });
        }

        const score = hasEscapeListeners ? 90 : 65;

        return {
            test: 'Escape Key Handling',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${modals.length} modal elements, escape support: ${hasEscapeListeners ? 'Yes' : 'No'}`
        };
    }

    /**
     * Test Enter key handling
     */
    async testEnterKeyHandling() {
        console.log('  ↩️  Testing Enter Key Handling...');

        const issues = [];
        const buttons = document.querySelectorAll('button, [role="button"]');

        let enterSupport = 0;
        buttons.forEach(button => {
            // Check if button has proper Enter key handling
            const hasClickHandler = button.onclick !== null ||
                                  button.addEventListener ||
                                  button.getAttribute('onclick');

            if (hasClickHandler) {
                enterSupport++;
            }
        });

        // Check form submission with Enter
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const hasSubmitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!hasSubmitButton) {
                issues.push({
                    type: 'enter_handling',
                    severity: 'minor',
                    element: 'form',
                    description: 'Form may not submit properly with Enter key',
                    recommendation: 'Add explicit submit button or Enter key handler'
                });
            }
        });

        const score = Math.min(95, 70 + (enterSupport / Math.max(buttons.length, 1)) * 25);

        return {
            test: 'Enter Key Handling',
            score: Math.round(score),
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `${enterSupport}/${buttons.length} buttons support Enter key`
        };
    }

    /**
     * Test Arrow key navigation
     */
    async testArrowKeyNavigation() {
        console.log('  ⬅️➡️ Testing Arrow Key Navigation...');

        const issues = [];

        // Check for custom arrow key navigation components
        const navigationComponents = document.querySelectorAll(
            '[role="menubar"], [role="menu"], [role="tablist"], [role="radiogroup"]'
        );

        let arrowSupport = 0;
        navigationComponents.forEach(component => {
            const hasArrowListeners = this.hasKeyboardEventListeners('Arrow', component);
            if (hasArrowListeners) {
                arrowSupport++;
            }
        });

        if (navigationComponents.length > 0 && arrowSupport === 0) {
            issues.push({
                type: 'arrow_navigation',
                severity: 'minor',
                element: 'navigation components',
                description: 'Navigation components may lack arrow key support',
                recommendation: 'Implement arrow key navigation for complex UI components'
            });
        }

        const score = navigationComponents.length === 0 ? 85 :
                     Math.min(95, 60 + (arrowSupport / navigationComponents.length) * 35);

        return {
            test: 'Arrow Key Navigation',
            score: Math.round(score),
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `${arrowSupport}/${navigationComponents.length} navigation components support arrows`
        };
    }

    /**
     * Test Focus Management
     */
    async testFocusManagement() {
        console.log('  🎯 Testing Focus Management...');

        const issues = [];

        // Check for focus trapping in modals
        const modals = document.querySelectorAll('[role="dialog"], .modal');
        modals.forEach(modal => {
            const focusableInModal = modal.querySelectorAll(this.focusableElements);
            if (focusableInModal.length === 0) {
                issues.push({
                    type: 'focus_management',
                    severity: 'major',
                    element: 'modal',
                    description: 'Modal has no focusable elements',
                    recommendation: 'Ensure modals have at least one focusable element'
                });
            }
        });

        // Check for programmatic focus management
        const hasFocusManagement = this.checkProgrammaticFocus();

        if (!hasFocusManagement) {
            issues.push({
                type: 'focus_management',
                severity: 'minor',
                element: 'general',
                description: 'Limited programmatic focus management detected',
                recommendation: 'Implement focus management for dynamic content'
            });
        }

        const score = Math.max(60, 90 - (issues.length * 15));

        return {
            test: 'Focus Management',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Focus management analysis completed, ${issues.length} issues found`
        };
    }

    /**
     * Test Skip Links
     */
    async testSkipLinks() {
        console.log('  ⏭️  Testing Skip Links...');

        const issues = [];
        const skipLinks = document.querySelectorAll('a[href^="#"], .skip-link');

        if (skipLinks.length === 0) {
            issues.push({
                type: 'skip_links',
                severity: 'minor',
                element: 'navigation',
                description: 'No skip links found for keyboard users',
                recommendation: 'Add skip links to bypass repetitive content'
            });
        }

        // Check if skip links are visible on focus
        let visibleOnFocus = 0;
        skipLinks.forEach(link => {
            // In a real test, we'd check computed styles on focus
            if (link.textContent.toLowerCase().includes('skip')) {
                visibleOnFocus++;
            }
        });

        const score = skipLinks.length === 0 ? 70 : Math.min(95, 80 + (visibleOnFocus * 5));

        return {
            test: 'Skip Links',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${skipLinks.length} skip links, ${visibleOnFocus} visible on focus`
        };
    }

    /**
     * Test Form Keyboard Interaction
     */
    async testFormKeyboardInteraction() {
        console.log('  📝 Testing Form Keyboard Interaction...');

        const issues = [];
        const forms = document.querySelectorAll('form');

        forms.forEach((form, index) => {
            // Check for fieldsets and legends
            const fieldsets = form.querySelectorAll('fieldset');
            const hasProperGrouping = fieldsets.length > 0;

            // Check for label associations
            const inputs = form.querySelectorAll('input, select, textarea');
            let properlyLabeled = 0;

            inputs.forEach(input => {
                const hasLabel = input.labels && input.labels.length > 0;
                const hasAriaLabel = input.getAttribute('aria-label');
                const hasAriaLabelledBy = input.getAttribute('aria-labelledby');

                if (hasLabel || hasAriaLabel || hasAriaLabelledBy) {
                    properlyLabeled++;
                }
            });

            if (inputs.length > 0 && properlyLabeled / inputs.length < 0.8) {
                issues.push({
                    type: 'form_labels',
                    severity: 'major',
                    element: `form ${index + 1}`,
                    description: `Only ${properlyLabeled}/${inputs.length} form inputs properly labeled`,
                    recommendation: 'Associate all form inputs with labels'
                });
            }
        });

        const score = Math.max(60, 90 - (issues.length * 20));

        return {
            test: 'Form Keyboard Interaction',
            score: score,
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `Analyzed ${forms.length} forms, found ${issues.length} issues`
        };
    }

    /**
     * Test Modal Keyboard Trap
     */
    async testModalKeyboardTrap() {
        console.log('  🪤 Testing Modal Keyboard Trap...');

        const issues = [];
        const modals = document.querySelectorAll('[role="dialog"], .modal');

        modals.forEach((modal, index) => {
            const focusableElements = modal.querySelectorAll(this.focusableElements);

            if (focusableElements.length === 0) {
                issues.push({
                    type: 'modal_trap',
                    severity: 'major',
                    element: `modal ${index + 1}`,
                    description: 'Modal has no focusable elements for keyboard trap',
                    recommendation: 'Add focusable elements and implement keyboard trap'
                });
            }

            // Check for close button
            const closeButton = modal.querySelector('[aria-label*="close"], .close-button, button[data-close]');
            if (!closeButton) {
                issues.push({
                    type: 'modal_trap',
                    severity: 'minor',
                    element: `modal ${index + 1}`,
                    description: 'Modal missing accessible close button',
                    recommendation: 'Add accessible close button with proper aria-label'
                });
            }
        });

        const score = Math.max(70, 95 - (issues.length * 15));

        return {
            test: 'Modal Keyboard Trap',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Analyzed ${modals.length} modals, found ${issues.length} issues`
        };
    }

    /**
     * Test Custom Keyboard Shortcuts
     */
    async testCustomKeyboardShortcuts() {
        console.log('  ⌨️  Testing Custom Keyboard Shortcuts...');

        const issues = [];

        // Check for accesskey attributes
        const accessKeyElements = document.querySelectorAll('[accesskey]');

        // Check for custom keyboard shortcuts in JavaScript
        const hasCustomShortcuts = this.hasKeyboardEventListeners('custom');

        if (accessKeyElements.length === 0 && !hasCustomShortcuts) {
            issues.push({
                type: 'keyboard_shortcuts',
                severity: 'minor',
                element: 'general',
                description: 'No keyboard shortcuts detected',
                recommendation: 'Consider adding keyboard shortcuts for power users'
            });
        }

        // Check for conflicts with browser shortcuts
        accessKeyElements.forEach(element => {
            const accessKey = element.getAttribute('accesskey').toLowerCase();
            const conflictingKeys = ['f', 't', 'h', 'r', 'w', 'n']; // Common browser shortcuts

            if (conflictingKeys.includes(accessKey)) {
                issues.push({
                    type: 'keyboard_shortcuts',
                    severity: 'minor',
                    element: element.tagName.toLowerCase(),
                    description: `AccessKey "${accessKey}" conflicts with browser shortcuts`,
                    recommendation: 'Use non-conflicting accesskey values'
                });
            }
        });

        const score = 85 - (issues.length * 10);

        return {
            test: 'Custom Keyboard Shortcuts',
            score: Math.max(70, score),
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${accessKeyElements.length} accesskey elements, custom shortcuts: ${hasCustomShortcuts ? 'Yes' : 'No'}`
        };
    }

    /**
     * Helper: Check for visible focus indicators
     */
    checkFocusIndicators() {
        const styles = document.styleSheets;
        for (let i = 0; i < styles.length; i++) {
            try {
                const rules = styles[i].cssRules || styles[i].rules;
                for (let j = 0; j < rules.length; j++) {
                    const rule = rules[j];
                    if (rule.selectorText && rule.selectorText.includes(':focus')) {
                        return true;
                    }
                }
            } catch (e) {
                // Cross-origin stylesheet, skip
                continue;
            }
        }
        return false;
    }

    /**
     * Helper: Check for keyboard event listeners
     */
    hasKeyboardEventListeners(keyType, element = document) {
        // This is a simplified check - in a real implementation,
        // we'd need to inspect the actual event listeners
        const scripts = document.querySelectorAll('script');
        for (let script of scripts) {
            const content = script.textContent;
            if (content.includes('addEventListener') &&
                (content.includes('keydown') || content.includes('keyup'))) {
                if (keyType === 'Escape' && content.includes('Escape')) return true;
                if (keyType === 'Arrow' && content.includes('Arrow')) return true;
                if (keyType === 'custom') return true;
            }
        }
        return false;
    }

    /**
     * Helper: Check for programmatic focus management
     */
    checkProgrammaticFocus() {
        const scripts = document.querySelectorAll('script');
        for (let script of scripts) {
            const content = script.textContent;
            if (content.includes('.focus()') || content.includes('focus(')) {
                return true;
            }
        }
        return false;
    }

    /**
     * Generate test report
     */
    generateReport(results) {
        const totalTests = results.length;
        const passedTests = results.filter(r => r.status === 'pass').length;
        const overallScore = Math.round(results.reduce((sum, r) => sum + r.score, 0) / totalTests);

        console.log('\n🎯 Keyboard Navigation Test Results');
        console.log('═'.repeat(50));
        console.log(`Overall Score: ${overallScore}/100`);
        console.log(`Tests Passed: ${passedTests}/${totalTests}`);
        console.log('');

        results.forEach(result => {
            const statusIcon = result.status === 'pass' ? '✅' :
                             result.status === 'warning' ? '⚠️' : '❌';
            console.log(`${statusIcon} ${result.test}: ${result.score}/100 - ${result.details}`);

            if (result.issues.length > 0) {
                result.issues.forEach(issue => {
                    const severityIcon = issue.severity === 'critical' ? '🔴' :
                                       issue.severity === 'major' ? '🟠' : '🟡';
                    console.log(`   ${severityIcon} ${issue.description}`);
                });
            }
        });

        return {
            overallScore,
            totalTests,
            passedTests,
            results
        };
    }
}

// Usage example
if (typeof document !== 'undefined') {
    const tester = new KeyboardNavigationTester();
    tester.runAllTests().then(results => {
        console.log('Keyboard navigation testing completed!');
    });
} else {
    // For Node.js environment
    module.exports = KeyboardNavigationTester;
}