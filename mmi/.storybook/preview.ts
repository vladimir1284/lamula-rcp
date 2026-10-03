import '../src/assets/main.css'
import type { Preview } from '@storybook/vue3-vite'

// Misma lógica que el script inline de index.html (default oscuro salvo
// preferencia guardada en claro), y en el mismo lugar: evaluación de
// módulo, no dentro del decorator. El decorator es una función que
// Storybook llama al construir el árbol de la story -- su orden relativo a
// la evaluación de useTheme.ts (importado transitivamente por
// GlobalStatusBar -> ThemeToggle) no está garantizado, y si useTheme lee
// el <html> antes de que esto corra, su estado interno queda desincronizado
// del <html> real (el toggle "miente"). Acá, a nivel de módulo, Storybook
// garantiza que corre antes de montar cualquier story.
try {
  if (localStorage.getItem('lamula-rcp:theme') !== 'light') {
    document.documentElement.classList.add('dark')
  }
} catch {
  document.documentElement.classList.add('dark')
}

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
    // `dark` ya quedó en el <html> real del iframe (arriba, a nivel de
    // módulo) -- acá sólo el wrapper de altura/fondo. <html> real y no un
    // div porque un <DialogPortal> (reka-ui, ej. StepWidthSetup.vue)
    // teletransporta su contenido a <body>, afuera de cualquier wrapper.
    () => ({ template: '<div class="bg-background" style="height:100vh"><story /></div>' }),
  ],
}

export default preview
