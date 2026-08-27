import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import type { StorybookConfig } from '@storybook/vue3-vite'

const config: StorybookConfig = {
  stories: ['../src/components/domain/**/*.stories.@(js|ts)'],
  addons: ['@storybook/addon-docs'],
  framework: '@storybook/vue3-vite',
  core: {
    // Air-gapped target (D-09) -- no phone-home, no Chromatic dependency. The build this produces
    // is a static bundle (`pnpm build-storybook`), nothing that needs a service or license key.
    disableTelemetry: true,
  },
  viteFinal: async (viteConfig) => {
    viteConfig.plugins ??= []
    viteConfig.plugins.push(tailwindcss())
    viteConfig.resolve ??= {}
    viteConfig.resolve.alias = {
      ...viteConfig.resolve.alias,
      '@': fileURLToPath(new URL('../src', import.meta.url)),
    }
    return viteConfig
  },
}
export default config
