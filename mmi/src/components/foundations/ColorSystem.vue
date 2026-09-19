<script setup lang="ts">
// Referencia viva de docs/diseno/inventario-ui.md §Requisitos transversales #1
// y §D6. No es un componente de producto: es la página de fundamentos que el
// resto del diseño consulta y contra la que se corre validate_palette.js.
// Ver notas de validación (ΔE, contraste) en el pie de cada bloque -- son
// resultado de cálculo (script dataviz), no estimación visual.

const states = [
  { key: 'ok', label: 'OK', class: 'bg-state-ok', note: 'Contraste 5.8:1 sobre scope oscuro' },
  { key: 'warn', label: 'WARN', class: 'bg-state-warn', note: 'Contraste 10.6:1' },
  { key: 'fault', label: 'FAULT', class: 'bg-state-fault', note: 'Contraste 4.1:1' },
  { key: 'disabled', label: 'DISABLED', class: 'bg-state-disabled', note: 'Gris neutro, invariante de tema' },
  { key: 'simulated', label: 'SIMULATED', class: 'bg-state-simulated', note: 'Acento violeta reservado; siempre con etiqueta "SIM"' },
]

const reflectivity = [
  { step: 1, class: 'bg-data-reflectivity-1', dbz: '< 5 dBZ (ruido)' },
  { step: 2, class: 'bg-data-reflectivity-2', dbz: '~15 dBZ' },
  { step: 3, class: 'bg-data-reflectivity-3', dbz: '~25 dBZ' },
  { step: 4, class: 'bg-data-reflectivity-4', dbz: '~35 dBZ' },
  { step: 5, class: 'bg-data-reflectivity-5', dbz: '~45 dBZ' },
  { step: 6, class: 'bg-data-reflectivity-6', dbz: '~55 dBZ' },
  { step: 7, class: 'bg-data-reflectivity-7', dbz: '~65 dBZ (granizo)' },
  { step: 8, class: 'bg-data-reflectivity-8', dbz: '> 70 dBZ (clip)' },
]

const velocity = [
  'bg-data-velocity-away-5',
  'bg-data-velocity-away-4',
  'bg-data-velocity-away-3',
  'bg-data-velocity-away-2',
  'bg-data-velocity-away-1',
  'bg-data-velocity-zero',
  'bg-data-velocity-toward-1',
  'bg-data-velocity-toward-2',
  'bg-data-velocity-toward-3',
  'bg-data-velocity-toward-4',
  'bg-data-velocity-toward-5',
]

const width = ['bg-data-width-1', 'bg-data-width-2', 'bg-data-width-3', 'bg-data-width-4']
</script>

<template>
  <div class="space-y-10 bg-background p-6 text-foreground">
    <section>
      <h2 class="mb-1 text-sm font-semibold">Estados de indicador (5 + simulated)</h2>
      <p class="mb-3 text-xs text-muted-foreground">
        `stale` no está aquí a propósito: nunca es un color propio, es la superposición
        <code>.is-stale</code> sobre el color de estado vigente. Ver demo abajo.
      </p>
      <div class="flex flex-wrap gap-4">
        <div v-for="s in states" :key="s.key" class="w-36">
          <div class="flex h-12 items-center justify-center rounded-md text-xs font-medium text-white" :class="s.class">
            {{ s.label }}
          </div>
          <p class="mt-1 text-[10px] text-muted-foreground">{{ s.note }}</p>
        </div>
      </div>
    </section>

    <section>
      <h2 class="mb-1 text-sm font-semibold">Stale (superposición, no color)</h2>
      <div class="flex flex-wrap gap-4">
        <div class="w-36 rounded-md bg-state-ok is-stale flex h-12 items-center justify-center text-xs font-medium text-white">
          OK · STALE
        </div>
        <div class="w-36 rounded-md bg-state-fault is-stale flex h-12 items-center justify-center text-xs font-medium text-white">
          FAULT · STALE
        </div>
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        El color de fondo original sigue siendo legible bajo el hatch; nunca se sustituye por gris.
      </p>
    </section>

    <section>
      <h2 class="mb-1 text-sm font-semibold">Nominal vs actual</h2>
      <div class="flex items-center gap-6 text-sm">
        <span class="value-nominal">42.0°</span>
        <span class="value-actual">41.8°</span>
        <span class="value-diverged px-2 py-0.5 text-xs">Δ 3.2° · difieren</span>
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        Guionado + gris = pedido. Sólido + negrita = en uso. Contorno warn = difieren más allá de tolerancia.
      </p>
    </section>

    <section>
      <h2 class="mb-1 text-sm font-semibold">Reflectividad — secuencial multi-hue (D6)</h2>
      <div class="flex overflow-hidden rounded-md">
        <div v-for="r in reflectivity" :key="r.step" class="flex h-14 flex-1 flex-col items-center justify-end pb-1" :class="r.class">
          <span class="text-[9px] text-black/70 mix-blend-luminosity">{{ r.dbz }}</span>
        </div>
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        Excepción documentada a "secuencial = un solo hue": convención meteorológica multi-hue,
        validada como rampa ordenada (ΔE adyacente ≥ 9.6 CVD, ≥ 15.9 visión normal, sobre scope
        oscuro #0d0d0d). Extremos con contraste bajo (ruido, extremo) llevan etiqueta numérica
        siempre visible como alivio.
      </p>
    </section>

    <section>
      <h2 class="mb-1 text-sm font-semibold">Velocidad — divergente, cero centrado (D6)</h2>
      <div class="flex overflow-hidden rounded-md">
        <div v-for="(v, i) in velocity" :key="i" class="h-10 flex-1" :class="v" />
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        Azul/rojo, no verde/rojo: el legacy usa verde/rojo, aquí se descarta porque colapsa bajo
        deuteranopia/protanopia. Polos validados ΔE 30.8 (CVD) / 39.0 (visión normal).
      </p>
    </section>

    <section>
      <h2 class="mb-1 text-sm font-semibold">Spectrum width — secuencial (D6)</h2>
      <div class="flex overflow-hidden rounded-md">
        <div v-for="(w, i) in width" :key="i" class="h-10 flex-1" :class="w" />
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        Hue violeta reservado para esta magnitud; no compartido con reflectividad ni velocidad.
        ΔE adyacente ≥ 15.1 (CVD) / 15.6 (visión normal).
      </p>
    </section>
  </div>
</template>
