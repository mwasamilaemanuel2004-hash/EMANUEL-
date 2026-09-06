// ESMH.TRADE — ESLint flat config (ESLint >= 9)
// Lints the vanilla-JS frontend. Run:  npx eslint frontend
// eslint-disable-next-line import/no-anonymous-default-export
export default [
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      '**/__pycache__/**',
      'mt5_live_trading_bot-main/**',
      'data/**',
      'logs/**',
      '**/pwa/manifest.json',
    ],
  },
  {
    files: ['frontend/**/*.js', 'src/**/*.js', '*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        fetch: 'readonly',
        WebSocket: 'readonly',
        console: 'readonly',
        alert: 'readonly',
        confirm: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
        requestAnimationFrame: 'readonly',
        performance: 'readonly',
        location: 'readonly',
        history: 'readonly',
        TextDecoder: 'readonly',
        // Node globals (helpers/scripts)
        require: 'readonly',
        module: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        Buffer: 'readonly',
      },
    },
    rules: {
      // Errors — code quality & safety
      'no-var': 'warn',
      'prefer-const': 'warn',
      'no-console': 'warn',
      'no-unused-vars': ['warn', { args: 'after-used', ignoreRestSiblings: true }],
      'no-dupe-keys': 'error',
      'no-duplicate-case': 'error',
      'no-func-assign': 'error',
      'no-implied-eval': 'error',
      'no-sequences': 'error',
      'no-unreachable': 'error',
      'no-useless-escape': 'warn',
      'no-multi-str': 'error',
      'no-new-func': 'error',
      'no-cond-assign': ['error', 'always'],
      'no-constant-condition': ['error', { checkLoops: false }],
      eqeqeq: ['warn', 'smart'],
      curly: ['warn', 'multi-line'],
    },
  },
]