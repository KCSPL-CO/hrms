<template>
	<div
		class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white text-center px-6"
	>
		<h1 class="text-2xl font-bold mb-3">
			{{ __("Install Frappe HR") }}
		</h1>

		<p class="text-gray-600 mb-6">
			{{ __("Install the app to continue using Frappe HR") }}
		</p>

		<!-- ANDROID / DESKTOP -->
		<Button
			v-if="canInstall"
			variant="solid"
			class="w-full py-5"
			@click="install"
		>
			<template #prefix>
				<FeatherIcon name="download" class="w-4" />
			</template>
			Install App
		</Button>

		<!-- iOS SAFARI -->
		<div v-if="isIos && isSafari && !isStandalone" class="w-full mt-6">
			<Button
				variant="outline"
				class="w-full py-4 flex items-center justify-center gap-2"
				@click="showIosHelp = !showIosHelp"
			>
				<FeatherIcon
					name="share"
					class="w-5 h-5 text-blue-600"
				/>
				Add to Home Screen
			</Button>

			<div
				v-if="showIosHelp"
				class="mt-4 rounded-lg bg-blue-50 px-4 py-3 text-sm text-left"
			>
				<p class="font-semibold mb-2">Follow these steps:</p>
				<ol class="list-decimal pl-4 space-y-1">
					<li>
						Tap Safari’s
						<FeatherIcon
							name="share"
							class="inline w-4 h-4 text-blue-600"
						/>
						button
					</li>
					<li>Select <b>Add to Home Screen</b></li>
					<li>Open Frappe HR from your Home Screen</li>
				</ol>
			</div>
		</div>

		<!-- iOS NON-SAFARI -->
		<p
			v-if="isIos && !isSafari"
			class="mt-4 text-sm text-red-600"
		>
			Please open this site in Safari to install the app.
		</p>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Button, FeatherIcon } from "frappe-ui"

const deferredPrompt = ref(null)
const canInstall = ref(false)
const showIosHelp = ref(false)

const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent)
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent)
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
		location.reload()
	})
})

async function install() {
	if (!deferredPrompt.value) return
	await deferredPrompt.value.prompt()
}
</script>
