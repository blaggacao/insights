<script setup>
const props = defineProps({
	title: { type: String },
	actions: { type: Array },
})
</script>

<template>
	<div class="flex h-14 flex-shrink-0 items-center justify-between">
		<div class="flex items-center space-x-4">
			<div class="text-3xl font-medium text-gray-900">{{ title }}</div>
			<slot name="title-items"></slot>
		</div>
		<div class="flex space-x-4">
			<Button
				v-for="action in actions"
				:key="action.label"
				class="shadow-sm"
				:appearance="action.appearance"
				:iconLeft="action.iconLeft"
				@click="action.handler"
			>
				{{ action.label }}
			</Button>
		</div>
	</div>
</template>
