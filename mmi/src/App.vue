<script setup lang="ts"></script>

<template>
  <nav class="flex gap-4 border-b p-3 text-sm">
    <RouterLink to="/" class="hover:underline">Control Center</RouterLink>
    <RouterLink to="/system-status" class="hover:underline">System Status &amp; BITE</RouterLink>
    <RouterLink to="/system-visualization" class="hover:underline">System Visualization</RouterLink>
    <RouterLink to="/scan-worksheet" class="hover:underline">Scan Worksheet</RouterLink>
    <RouterLink to="/antenna-control" class="hover:underline">Antenna Control</RouterLink>
    <RouterLink to="/system-information" class="hover:underline">System Information</RouterLink>
  </nav>
  <RouterView />
</template>
