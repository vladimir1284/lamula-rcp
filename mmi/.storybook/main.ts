import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import type { StorybookConfig } from '@storybook/vue3-vite'

const config: StorybookConfig = {
  stories: [
    '../src/components/{domain,foundations,shell}/**/*.stories.@(js|ts)',
    '../src/views/**/*.stories.@(js|ts)',
    '../src/*.stories.@(js|ts)',
  ],
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
    // Orden importa: el alias exacto de useGateway va antes que el prefijo
    // '@' genérico, para que sólo ESE import se redirija al doble de
    // Storybook (useGateway.mock.ts) -- ver el comentario de cabecera de ese
    // fichero. Todo lo demás bajo '@/...' sigue resolviendo al código real.
    viteConfig.resolve.alias = [
      {
        find: '@/composables/useGateway',
        replacement: fileURLToPath(new URL('../src/composables/useGateway.mock.ts', import.meta.url)),
      },
      { find: '@', replacement: fileURLToPath(new URL('../src', import.meta.url)) },
    ]
    return viteConfig
  },
}
export default config
