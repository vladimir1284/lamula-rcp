<script setup lang="ts">
// Tema claro/oscuro ternable (docs/diseno/inventario-ui.md): el default
// operativo es oscuro, pero no va cableado -- useTheme() persiste la
// preferencia en localStorage.
import { Button } from '@/components/ui/button'
import { useTheme } from '@/composables/useTheme'

const { theme, toggle } = useTheme()
</script>

<template>
  <Button
    variant="ghost"
    size="sm"
    :title="theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
    @click="toggle"
  >
    {{ theme === 'dark' ? 'Modo claro' : 'Modo oscuro' }}
  </Button>
</template>
