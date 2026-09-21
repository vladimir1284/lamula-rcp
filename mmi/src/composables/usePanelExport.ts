import { inject, provide, unref, type Ref } from 'vue'

export const PANEL_EXPORT_DATA_KEY = Symbol('PANEL_EXPORT_DATA_KEY')

export function providePanelExportData(dataRef: Ref<unknown> | (() => unknown)): void {
  provide(PANEL_EXPORT_DATA_KEY, dataRef)
}

export function useInjectPanelExportData(): unknown {
  const injected = inject<Ref<unknown> | (() => unknown) | undefined>(PANEL_EXPORT_DATA_KEY, undefined)
  if (!injected) return undefined
  if (typeof injected === 'function') {
    return injected()
  }
  return unref(injected)
}
