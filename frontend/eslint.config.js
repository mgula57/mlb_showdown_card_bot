import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { globalIgnores } from 'eslint/config'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactRefresh.configs.vite,
    ],
    // eslint-plugin-react-hooks's `configs['recommended-latest']` still ships an eslintrc-style
    // `plugins: ['react-hooks']` array (as of 7.1.1), which flat config rejects. Register the
    // plugin and pull its rules in manually instead of spreading the broken config via `extends`.
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: reactHooks.configs['recommended-latest'].rules,
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
])
