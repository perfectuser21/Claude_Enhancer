module.exports = {
  default: {
    paths: ['acceptance/features/**/*.feature'],
    require: ['acceptance/steps/**/*.js'],
    format: ['progress-bar', 'html:test/reports/cucumber.html'],
    publishQuiet: true
  },
  ci: {
    paths: ['acceptance/features/**/*.feature'],
    require: ['acceptance/steps/**/*.js'],
    format: ['progress', 'json:test/reports/cucumber_report.json'],
    publishQuiet: true,
    strict: true,
    retry: 2
  }
};