/**
 * Screen Reader Compatibility Test Suite
 * Tests screen reader accessibility for Claude Enhancer 5.0
 */

class ScreenReaderTester {
    constructor() {
        this.testResults = [];
        this.ariaAttributes = [
            'aria-label', 'aria-labelledby', 'aria-describedby',
            'aria-expanded', 'aria-hidden', 'aria-live',
            'aria-role', 'aria-current', 'aria-selected',
            'aria-checked', 'aria-pressed', 'aria-disabled'
        ];
    }

    /**
     * Run comprehensive screen reader tests
     */
    async runAllTests() {
        console.log('🔊 Starting Screen Reader Compatibility Tests...');

        const tests = [
            this.testARIALabels(),
            this.testHeadingStructure(),
            this.testLandmarks(),
            this.testLiveRegions(),
            this.testFormLabeling(),
            this.testImageAltText(),
            this.testTableHeaders(),
            this.testButtonDescriptions(),
            this.testErrorAnnouncements()
        ];

        const results = await Promise.all(tests);
        this.generateReport(results);
        return results;
    }

    /**
     * Test ARIA labels and descriptions
     */
    async testARIALabels() {
        console.log('  🏷️  Testing ARIA Labels...');

        const issues = [];

        // Check interactive elements for proper labeling
        const interactiveElements = document.querySelectorAll(
            'button, input, select, textarea, a, [role="button"], [role="link"], [role="tab"]'
        );

        let properlyLabeled = 0;

        interactiveElements.forEach((element, index) => {
            const hasLabel = this.hasAccessibleName(element);

            if (hasLabel) {
                properlyLabeled++;
            } else {
                const elementType = element.tagName.toLowerCase();
                const role = element.getAttribute('role') || elementType;

                issues.push({
                    type: 'aria_labeling',
                    severity: 'major',
                    element: `${role} (${index + 1})`,
                    description: `Interactive ${role} element lacks accessible name`,
                    recommendation: 'Add aria-label, aria-labelledby, or visible text content'
                });
            }
        });

        // Check for proper ARIA attribute usage
        const elementsWithAria = document.querySelectorAll('[aria-*]');
        let validAriaUsage = 0;

        elementsWithAria.forEach(element => {
            const ariaAttrs = Array.from(element.attributes).filter(attr =>
                attr.name.startsWith('aria-')
            );

            ariaAttrs.forEach(attr => {
                if (this.ariaAttributes.includes(attr.name)) {
                    validAriaUsage++;
                } else {
                    issues.push({
                        type: 'aria_usage',
                        severity: 'minor',
                        element: element.tagName.toLowerCase(),
                        description: `Unknown or invalid ARIA attribute: ${attr.name}`,
                        recommendation: 'Use valid ARIA attributes from ARIA specification'
                    });
                }
            });
        });

        const labelingScore = interactiveElements.length > 0 ?
            Math.round((properlyLabeled / interactiveElements.length) * 100) : 100;

        const score = Math.min(labelingScore, 95);

        return {
            test: 'ARIA Labels',
            score: score,
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `${properlyLabeled}/${interactiveElements.length} interactive elements properly labeled`
        };
    }

    /**
     * Test heading structure for screen readers
     */
    async testHeadingStructure() {
        console.log('  📋 Testing Heading Structure...');

        const issues = [];
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]');

        if (headings.length === 0) {
            issues.push({
                type: 'heading_structure',
                severity: 'major',
                element: 'page structure',
                description: 'No headings found on page',
                recommendation: 'Add proper heading structure for screen reader navigation'
            });

            return {
                test: 'Heading Structure',
                score: 40,
                status: 'fail',
                issues: issues,
                details: 'No headings found'
            };
        }

        // Check for h1 element
        const h1Elements = document.querySelectorAll('h1');
        if (h1Elements.length === 0) {
            issues.push({
                type: 'heading_structure',
                severity: 'major',
                element: 'main heading',
                description: 'No H1 heading found',
                recommendation: 'Add H1 heading as main page title'
            });
        } else if (h1Elements.length > 1) {
            issues.push({
                type: 'heading_structure',
                severity: 'minor',
                element: 'main heading',
                description: `Multiple H1 headings found (${h1Elements.length})`,
                recommendation: 'Use only one H1 per page'
            });
        }

        // Check heading hierarchy
        const headingLevels = Array.from(headings).map(h => {
            if (h.hasAttribute('role')) {
                const level = h.getAttribute('aria-level');
                return level ? parseInt(level) : 1;
            }
            return parseInt(h.tagName.charAt(1));
        });

        let hierarchyIssues = 0;
        for (let i = 1; i < headingLevels.length; i++) {
            if (headingLevels[i] - headingLevels[i-1] > 1) {
                hierarchyIssues++;
                issues.push({
                    type: 'heading_hierarchy',
                    severity: 'minor',
                    element: `heading ${i + 1}`,
                    description: `Heading level skips from H${headingLevels[i-1]} to H${headingLevels[i]}`,
                    recommendation: 'Use sequential heading levels without skipping'
                });
            }
        }

        const score = Math.max(60, 95 - (hierarchyIssues * 10) - (h1Elements.length !== 1 ? 15 : 0));

        return {
            test: 'Heading Structure',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${headings.length} headings with ${hierarchyIssues} hierarchy issues`
        };
    }

    /**
     * Test ARIA landmarks
     */
    async testLandmarks() {
        console.log('  🗺️  Testing ARIA Landmarks...');

        const issues = [];
        const landmarks = {
            main: document.querySelectorAll('main, [role="main"]'),
            nav: document.querySelectorAll('nav, [role="navigation"]'),
            header: document.querySelectorAll('header, [role="banner"]'),
            footer: document.querySelectorAll('footer, [role="contentinfo"]'),
            aside: document.querySelectorAll('aside, [role="complementary"]'),
            search: document.querySelectorAll('[role="search"]')
        };

        // Check for required landmarks
        if (landmarks.main.length === 0) {
            issues.push({
                type: 'landmarks',
                severity: 'major',
                element: 'main landmark',
                description: 'No main landmark found',
                recommendation: 'Add <main> element or role="main" to identify main content'
            });
        }

        if (landmarks.main.length > 1) {
            issues.push({
                type: 'landmarks',
                severity: 'minor',
                element: 'main landmark',
                description: `Multiple main landmarks found (${landmarks.main.length})`,
                recommendation: 'Use only one main landmark per page'
            });
        }

        // Check for navigation landmarks
        if (landmarks.nav.length === 0) {
            issues.push({
                type: 'landmarks',
                severity: 'minor',
                element: 'navigation landmark',
                description: 'No navigation landmarks found',
                recommendation: 'Add <nav> elements or role="navigation" for navigation areas'
            });
        }

        // Check landmark labeling
        Object.entries(landmarks).forEach(([type, elements]) => {
            elements.forEach((element, index) => {
                if (elements.length > 1) {
                    const hasLabel = element.getAttribute('aria-label') ||
                                   element.getAttribute('aria-labelledby');
                    if (!hasLabel) {
                        issues.push({
                            type: 'landmark_labeling',
                            severity: 'minor',
                            element: `${type} landmark ${index + 1}`,
                            description: `Multiple ${type} landmarks should be labeled`,
                            recommendation: 'Add aria-label to distinguish multiple landmarks of same type'
                        });
                    }
                }
            });
        });

        const totalLandmarks = Object.values(landmarks).reduce((sum, arr) => sum + arr.length, 0);
        const score = Math.max(65, 90 - (issues.length * 8));

        return {
            test: 'ARIA Landmarks',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${totalLandmarks} landmarks, ${issues.length} issues`
        };
    }

    /**
     * Test live regions for dynamic content
     */
    async testLiveRegions() {
        console.log('  📢 Testing Live Regions...');

        const issues = [];
        const liveRegions = document.querySelectorAll('[aria-live], [role="status"], [role="alert"]');

        // Check for live regions
        if (liveRegions.length === 0) {
            issues.push({
                type: 'live_regions',
                severity: 'minor',
                element: 'dynamic content',
                description: 'No live regions found for dynamic content announcements',
                recommendation: 'Add aria-live regions for status updates and notifications'
            });
        }

        // Check live region configuration
        liveRegions.forEach((region, index) => {
            const liveValue = region.getAttribute('aria-live');
            const role = region.getAttribute('role');

            if (liveValue && !['polite', 'assertive', 'off'].includes(liveValue)) {
                issues.push({
                    type: 'live_regions',
                    severity: 'minor',
                    element: `live region ${index + 1}`,
                    description: `Invalid aria-live value: ${liveValue}`,
                    recommendation: 'Use "polite", "assertive", or "off" for aria-live'
                });
            }

            // Check for atomic attribute when needed
            if (liveValue === 'assertive' && !region.hasAttribute('aria-atomic')) {
                issues.push({
                    type: 'live_regions',
                    severity: 'minor',
                    element: `live region ${index + 1}`,
                    description: 'Assertive live region missing aria-atomic attribute',
                    recommendation: 'Consider adding aria-atomic="true" for complete announcements'
                });
            }
        });

        const score = liveRegions.length > 0 ? Math.max(75, 90 - (issues.length * 10)) : 70;

        return {
            test: 'Live Regions',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${liveRegions.length} live regions, ${issues.length} configuration issues`
        };
    }

    /**
     * Test form labeling for screen readers
     */
    async testFormLabeling() {
        console.log('  📝 Testing Form Labeling...');

        const issues = [];
        const formControls = document.querySelectorAll('input, select, textarea');

        let properlyLabeled = 0;

        formControls.forEach((control, index) => {
            const type = control.type;

            // Skip hidden inputs
            if (type === 'hidden') return;

            const hasLabel = this.hasAccessibleName(control);
            const hasDescription = control.getAttribute('aria-describedby');

            if (hasLabel) {
                properlyLabeled++;
            } else {
                issues.push({
                    type: 'form_labeling',
                    severity: 'major',
                    element: `${type || 'input'} field ${index + 1}`,
                    description: `Form control lacks accessible label`,
                    recommendation: 'Associate with <label> element or add aria-label'
                });
            }

            // Check for required field indication
            if (control.hasAttribute('required') && !control.getAttribute('aria-required')) {
                issues.push({
                    type: 'form_labeling',
                    severity: 'minor',
                    element: `${type || 'input'} field ${index + 1}`,
                    description: 'Required field not announced to screen readers',
                    recommendation: 'Add aria-required="true" to required fields'
                });
            }

            // Check for error associations
            if (control.getAttribute('aria-invalid') === 'true' && !hasDescription) {
                issues.push({
                    type: 'form_labeling',
                    severity: 'major',
                    element: `${type || 'input'} field ${index + 1}`,
                    description: 'Invalid field lacks error description',
                    recommendation: 'Use aria-describedby to associate error messages'
                });
            }
        });

        const visibleControls = formControls.length - document.querySelectorAll('input[type="hidden"]').length;
        const labelingScore = visibleControls > 0 ?
            Math.round((properlyLabeled / visibleControls) * 100) : 100;

        const score = Math.min(labelingScore, 95);

        return {
            test: 'Form Labeling',
            score: score,
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `${properlyLabeled}/${visibleControls} form controls properly labeled`
        };
    }

    /**
     * Test image alt text
     */
    async testImageAltText() {
        console.log('  🖼️  Testing Image Alt Text...');

        const issues = [];
        const images = document.querySelectorAll('img');

        let properImages = 0;

        images.forEach((img, index) => {
            const alt = img.getAttribute('alt');
            const role = img.getAttribute('role');

            if (alt === null) {
                issues.push({
                    type: 'image_alt',
                    severity: 'major',
                    element: `image ${index + 1}`,
                    description: 'Image missing alt attribute',
                    recommendation: 'Add alt attribute (empty for decorative images)'
                });
            } else if (alt === '' && role !== 'presentation') {
                // Empty alt is acceptable for decorative images
                properImages++;
            } else if (alt !== '') {
                properImages++;

                // Check for bad alt text patterns
                const badPatterns = ['image of', 'picture of', 'photo of', 'graphic of'];
                const lowerAlt = alt.toLowerCase();

                if (badPatterns.some(pattern => lowerAlt.includes(pattern))) {
                    issues.push({
                        type: 'image_alt',
                        severity: 'minor',
                        element: `image ${index + 1}`,
                        description: 'Alt text contains redundant phrases',
                        recommendation: 'Remove redundant phrases like "image of" from alt text'
                    });
                }
            }
        });

        const score = images.length > 0 ?
            Math.round((properImages / images.length) * 100) : 100;

        return {
            test: 'Image Alt Text',
            score: Math.min(score, 95),
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `${properImages}/${images.length} images have proper alt text`
        };
    }

    /**
     * Test table headers and structure
     */
    async testTableHeaders() {
        console.log('  📊 Testing Table Structure...');

        const issues = [];
        const tables = document.querySelectorAll('table');

        if (tables.length === 0) {
            return {
                test: 'Table Headers',
                score: 100,
                status: 'pass',
                issues: [],
                details: 'No tables found'
            };
        }

        tables.forEach((table, index) => {
            // Check for table headers
            const headers = table.querySelectorAll('th');
            const rows = table.querySelectorAll('tr');

            if (headers.length === 0) {
                issues.push({
                    type: 'table_headers',
                    severity: 'major',
                    element: `table ${index + 1}`,
                    description: 'Table missing header cells (<th>)',
                    recommendation: 'Use <th> elements for table headers'
                });
            }

            // Check for table caption
            const caption = table.querySelector('caption');
            if (!caption && !table.getAttribute('aria-label') && !table.getAttribute('aria-labelledby')) {
                issues.push({
                    type: 'table_headers',
                    severity: 'minor',
                    element: `table ${index + 1}`,
                    description: 'Table missing caption or accessible name',
                    recommendation: 'Add <caption> element or aria-label for table description'
                });
            }

            // Check for complex table structure
            const complexTable = table.querySelector('th[scope], th[headers]');
            if (rows.length > 3 && headers.length > 2 && !complexTable) {
                issues.push({
                    type: 'table_headers',
                    severity: 'minor',
                    element: `table ${index + 1}`,
                    description: 'Complex table may need scope or headers attributes',
                    recommendation: 'Add scope attributes to headers in complex tables'
                });
            }
        });

        const score = Math.max(70, 95 - (issues.length * 15));

        return {
            test: 'Table Headers',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Analyzed ${tables.length} tables, found ${issues.length} issues`
        };
    }

    /**
     * Test button descriptions and states
     */
    async testButtonDescriptions() {
        console.log('  🔘 Testing Button Descriptions...');

        const issues = [];
        const buttons = document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]');

        let properButtons = 0;

        buttons.forEach((button, index) => {
            const hasAccessibleName = this.hasAccessibleName(button);

            if (!hasAccessibleName) {
                issues.push({
                    type: 'button_descriptions',
                    severity: 'major',
                    element: `button ${index + 1}`,
                    description: 'Button lacks accessible name',
                    recommendation: 'Add text content, aria-label, or aria-labelledby'
                });
            } else {
                properButtons++;
            }

            // Check for toggle buttons
            const pressed = button.getAttribute('aria-pressed');
            if (pressed !== null && !['true', 'false', 'mixed'].includes(pressed)) {
                issues.push({
                    type: 'button_descriptions',
                    severity: 'minor',
                    element: `button ${index + 1}`,
                    description: `Invalid aria-pressed value: ${pressed}`,
                    recommendation: 'Use "true", "false", or "mixed" for aria-pressed'
                });
            }

            // Check for expandable buttons
            const expanded = button.getAttribute('aria-expanded');
            if (expanded !== null && !['true', 'false'].includes(expanded)) {
                issues.push({
                    type: 'button_descriptions',
                    severity: 'minor',
                    element: `button ${index + 1}`,
                    description: `Invalid aria-expanded value: ${expanded}`,
                    recommendation: 'Use "true" or "false" for aria-expanded'
                });
            }
        });

        const score = buttons.length > 0 ?
            Math.round((properButtons / buttons.length) * 100) : 100;

        return {
            test: 'Button Descriptions',
            score: Math.min(score, 95),
            status: score >= 80 ? 'pass' : score >= 60 ? 'warning' : 'fail',
            issues: issues,
            details: `${properButtons}/${buttons.length} buttons properly described`
        };
    }

    /**
     * Test error announcements
     */
    async testErrorAnnouncements() {
        console.log('  ⚠️  Testing Error Announcements...');

        const issues = [];

        // Check for error elements
        const errorElements = document.querySelectorAll(
            '.error, [role="alert"], [aria-live="assertive"], .alert, .notification'
        );

        // Check for form validation
        const invalidInputs = document.querySelectorAll('[aria-invalid="true"]');

        invalidInputs.forEach((input, index) => {
            const describedBy = input.getAttribute('aria-describedby');
            if (!describedBy) {
                issues.push({
                    type: 'error_announcements',
                    severity: 'major',
                    element: `invalid input ${index + 1}`,
                    description: 'Invalid form field not associated with error message',
                    recommendation: 'Use aria-describedby to link error messages'
                });
            } else {
                const errorMessage = document.getElementById(describedBy);
                if (!errorMessage) {
                    issues.push({
                        type: 'error_announcements',
                        severity: 'major',
                        element: `invalid input ${index + 1}`,
                        description: 'aria-describedby references non-existent element',
                        recommendation: 'Ensure error message element exists with correct ID'
                    });
                }
            }
        });

        // Check for alert regions
        const alerts = document.querySelectorAll('[role="alert"]');
        if (invalidInputs.length > 0 && alerts.length === 0 && errorElements.length === 0) {
            issues.push({
                type: 'error_announcements',
                severity: 'minor',
                element: 'error handling',
                description: 'No alert regions found for error announcements',
                recommendation: 'Add role="alert" or aria-live regions for error messages'
            });
        }

        const score = Math.max(70, 95 - (issues.length * 12));

        return {
            test: 'Error Announcements',
            score: score,
            status: score >= 80 ? 'pass' : 'warning',
            issues: issues,
            details: `Found ${invalidInputs.length} invalid inputs, ${errorElements.length} error elements`
        };
    }

    /**
     * Helper: Check if element has accessible name
     */
    hasAccessibleName(element) {
        // Check for aria-label
        if (element.getAttribute('aria-label')) return true;

        // Check for aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = document.getElementById(labelledBy);
            return labelElement && labelElement.textContent.trim() !== '';
        }

        // Check for associated label
        if (element.labels && element.labels.length > 0) return true;

        // Check for text content
        const textContent = element.textContent.trim();
        if (textContent !== '') return true;

        // Check for alt attribute (for images)
        const alt = element.getAttribute('alt');
        if (alt !== null) return true;

        // Check for title attribute (last resort)
        const title = element.getAttribute('title');
        if (title && title.trim() !== '') return true;

        return false;
    }

    /**
     * Generate test report
     */
    generateReport(results) {
        const totalTests = results.length;
        const passedTests = results.filter(r => r.status === 'pass').length;
        const overallScore = Math.round(results.reduce((sum, r) => sum + r.score, 0) / totalTests);

        console.log('\n🔊 Screen Reader Compatibility Test Results');
        console.log('═'.repeat(55));
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

        console.log('\n📋 Screen Reader Recommendations:');
        console.log('• Test with actual screen readers (NVDA, JAWS, VoiceOver)');
        console.log('• Use semantic HTML elements where possible');
        console.log('• Ensure all interactive elements have accessible names');
        console.log('• Implement proper heading hierarchy');
        console.log('• Add ARIA landmarks for navigation');

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
    const tester = new ScreenReaderTester();
    tester.runAllTests().then(results => {
        console.log('Screen reader compatibility testing completed!');
    });
} else {
    // For Node.js environment
    module.exports = ScreenReaderTester;
}