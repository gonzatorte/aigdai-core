const js = require('@eslint/js');
const tseslint = require('@typescript-eslint/eslint-plugin');
const tsparser = require('@typescript-eslint/parser');
const react = require('eslint-plugin-react');
const reactHooks = require('eslint-plugin-react-hooks');
const prettier = require('eslint-plugin-prettier');
const prettierConfig = require('eslint-config-prettier');

module.exports = [
  js.configs.recommended,
  prettierConfig,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        document: 'readonly',
        window: 'readonly',
        console: 'readonly',
        process: 'readonly',
        SVGSVGElement: 'readonly',
        SVGLineElement: 'readonly',
        SVGCircleElement: 'readonly',
        SVGTextElement: 'readonly',
        SVGPathElement: 'readonly',
        SVGGElement: 'readonly',
        SVGRectElement: 'readonly',
        HTMLDivElement: 'readonly',
        HTMLInputElement: 'readonly',
        KeyboardEvent: 'readonly',
        IntersectionObserver: 'readonly',
        fetch: 'readonly',
        AbortController: 'readonly',
        RequestInit: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        MouseEvent: 'readonly',
        Option: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      react,
      'react-hooks': reactHooks,
      prettier,
    },
          rules: {
        ...tseslint.configs.recommended.rules,
        ...react.configs.recommended.rules,
        ...reactHooks.configs.recommended.rules,
        'react/react-in-jsx-scope': 'off',
        'react/prop-types': 'off',
        '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/explicit-module-boundary-types': 'off',
        '@typescript-eslint/no-explicit-any': 'off', // Allow any for flexible API library
        'prettier/prettier': 'error',
      },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
]; 