import '../src/assets/main.css'
import type { Preview } from '@storybook/vue3-vite'

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [
    // AppShell y otros layouts a pantalla completa dependen de `height:
    // 100%` en cascada desde <html>/<body> (ver main.css). El punto de
    // montaje real es #app; en Storybook es #storybook-root, que no hereda
    // esa regla -- se la damos aquí en vez de acoplar main.css a un id de
    // Storybook.
    () => ({ template: '<div style="height:100vh"><story /></div>' }),
  ],
}

export default preview
