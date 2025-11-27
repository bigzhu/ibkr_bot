<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-toolbar-title> DeMark 交易机器人 </q-toolbar-title>
        <q-space />
        <q-btn flat round dense icon="more_vert" @click="showMenu = !showMenu" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const showMenu = ref(false);
</script>
