<template>
	<ion-app>
		<!-- 🚫 Block app until installed -->
		<InstallPrompt v-if="!isInstalled" />

		<!-- ✅ Show app only after install -->
		<template v-else>
			<ion-router-outlet id="main-content" />
			<Toasts />
		</template>
	</ion-app>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import { Toasts } from "frappe-ui"

import InstallPrompt from "@/components/InstallPrompt.vue"
import { showNotification } from "@/utils/pushNotifications"

const isInstalled = ref(false)

onMounted(() => {
	isInstalled.value =
		window.matchMedia("(display-mode: standalone)").matches ||
		window.navigator.standalone === true

	window?.frappePushNotification?.onMessage((payload) => {
		showNotification(payload)
	})
})
</script>
