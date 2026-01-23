<template>
	<div class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white text-center px-6">
		<h1 class="text-2xl font-bold mb-3">
			{{ __("Install Frappe HR") }}
		</h1>

		<p class="text-gray-600 mb-6">
			{{ __("Install the app to continue using Frappe HR") }}
		</p>

		<!-- Android / Desktop -->
		<Button
			v-if="canInstall"
			variant="solid"
			class="w-full py-5"
			@click="install"
		>
			<template #prefix>
				<FeatherIcon name="download" class="w-4" />
			</template>
			{{ __("Install App") }}
		</Button>

		<!-- iOS -->
		<div v-if="isIos && !isStandalone" class="text-sm text-gray-700 mt-4">
			<p class="mb-2">
				{{ __("To install on iPhone:") }}
			</p>
			<p class="flex items-center justify-center gap-1">
				Tap <FeatherIcon name="share" class="w-4 h-4 text-blue-600" />
				<span>{{ __('then "Add to Home Screen"') }}</span>
			</p>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Button, FeatherIcon } from "frappe-ui"

const deferredPrompt = ref(null)
const canInstall = ref(false)

const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent)
const isStandalone =
	window.matchMedia("(display-mode: standalone)").matches ||
	window.navigator.standalone === true

onMounted(() => {
	window.addEventListener("beforeinstallprompt", (e) => {
		e.preventDefault()
		deferredPrompt.value = e
		canInstall.value = true
	})

	window.addEventListener("appinstalled", () => {
		location.reload() // 🔥 reload to unlock app
	})
})

async function install() {
	if (!deferredPrompt.value) return
	await deferredPrompt.value.prompt()
}
</script>
