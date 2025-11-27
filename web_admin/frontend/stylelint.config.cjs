module.exports = {
  extends: ['stylelint-config-standard-scss', 'stylelint-config-html'],
  overrides: [
    {
      files: ['**/*.vue'],
      customSyntax: 'postcss-html',
    },
  ],
  rules: {
    'selector-pseudo-class-no-unknown': [true, { ignorePseudoClasses: ['deep'] }],
    'selector-class-pattern': null,
  },
};
