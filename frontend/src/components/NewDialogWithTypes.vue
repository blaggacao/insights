<script setup>
import { computed } from 'vue'

const props = defineProps({
	show: {
		type: Boolean,
		default: false,
	},
	title: {
		type: String,
	},
	types: {
		type: Array,
		default: () => [],
	},
})
const emit = defineEmits(['update:show'])
const show = computed({
	get: () => props.show,
	set: (value) => emit('update:show', value),
})
</script>
<template>
	<Dialog v-model="show">
		<template #body>
			<div class="bg-white px-4 py-5 text-base sm:p-6">
				<h3 v-if="title" class="text-lg font-medium leading-6 text-gray-900">
					{{ title }}
				</h3>
				<!-- There are three types of query builder -->
				<div class="mt-4 grid grid-cols-1 gap-6">
					<div
						v-for="(type, index) in types"
						:key="index"
						class="group flex cursor-pointer items-center space-x-4"
						@click="type.handler()"
					>
						<div
							class="rounded-md border p-4 text-gray-400 shadow-sm transition-all group-hover:scale-105"
						>
							<FeatherIcon :name="type.icon" class="h-6 w-6 text-gray-400" />
						</div>
						<div>
							<div class="flex items-center space-x-2">
								<p
									class="text-lg font-medium leading-6 text-gray-900 transition-colors group-hover:text-blue-500"
								>
									{{ type.label }}
								</p>
								<Badge
									v-if="type.tag"
									color="green"
									class="!rounded-full !px-2 !py-0.5"
								>
									{{ type.tag }}
								</Badge>
							</div>
							<p class="text-sm leading-5 text-gray-500">
								{{ type.description }}
							</p>
						</div>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>
