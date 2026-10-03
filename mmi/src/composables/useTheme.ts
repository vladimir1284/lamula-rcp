import { ref, watchEffect } from 'vue'

// Preferencia de tema claro/oscuro -- singleton de módulo, mismo patrón que
// useGateway(). El default real (oscuro, sala de operación nocturna) lo
// decide el script inline de index.html antes del primer paint (evita
// flash); acá sólo se lee ese estado inicial y se mantiene en sync con
// localStorage de ahí en más.
const STORAGE_KEY = 'lamula-rcp:theme'

export type Theme = 'light' | 'dark'

function readInitial(): Theme {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    // localStorage puede no estar disponible (modo privado, cuota) -- se
    // sigue de la clase que index.html ya aplicó.
  }
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

const theme = ref<Theme>(readInitial())

watchEffect(() => {
  document.documentElement.classList.toggle('dark', theme.value === 'dark')
  try {
    window.localStorage.setItem(STORAGE_KEY, theme.value)
  } catch {
    // Sin persistencia entre recargas en ese caso -- la preferencia de la
    // sesión actual sigue funcionando igual.
  }
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  function set(value: Theme) {
    theme.value = value
  }
  return { theme, toggle, set }
}
