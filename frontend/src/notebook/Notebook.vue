<script setup lang="jsx">
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import ListView from '@/components/ListView.vue'
import useNotebook from '@/notebook/useNotebook'
import useNotebooks from '@/notebook/useNotebooks'
import { updateDocumentTitle } from '@/utils'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ notebook: String })
const router = useRouter()
const notebook = useNotebook(props.notebook)
notebook.reload()

const TitleWithIcon = (props) => (
	<div class="flex items-center">
		<FeatherIcon name="file-text" class="h-4 w-4 text-gray-600" />
		<span class="ml-3">{props.row.title}</span>
	</div>
)
const columns = [
	{ label: 'Title', key: 'title', cellComponent: TitleWithIcon },
	{ label: 'Created', key: 'created_from_now' },
	{ label: 'Modified', key: 'modified_from_now' },
]

async function createNotebookPage() {
	const page_name = await notebook.createPage(props.notebook)
	router.push({
		name: 'NotebookPage',
		params: {
			notebook: props.notebook,
			page: page_name,
		},
	})
}

const showDeleteDialog = ref(false)
async function handleDelete() {
	await notebook.deleteNotebook()
	showDeleteDialog.value = false
	await useNotebooks().reload()
	router.push({ name: 'NotebookList' })
}

const pageMeta = ref({ title: 'Notebook' })
updateDocumentTitle(pageMeta)
</script>

<template>
	<div class="h-full w-full bg-white px-6 py-4">
		<Breadcrumbs
			:items="[{ label: 'Notebooks', href: '/notebook' }, { label: notebook.doc.title }]"
		></Breadcrumbs>
		<ListView
			title="Pages"
			:actions="[
				{
					label: 'New Page',
					appearance: 'white',
					iconLeft: 'plus',
					handler: () => createNotebookPage(),
				},
			]"
			:columns="columns"
			:data="notebook.pages"
			:rowClick="
				({ name }) =>
					router.push({
						name: 'NotebookPage',
						params: {
							notebook: props.notebook,
							page: name,
						},
					})
			"
		>
			<template #title>
				<div class="flex items-center space-x-4">
					<div class="text-3xl font-medium text-gray-900">{{ notebook.doc.title }}</div>
					<Dropdown
						placement="left"
						:button="{ icon: 'more-horizontal', appearance: 'minimal' }"
						:options="[
							{
								label: 'Delete',
								icon: 'trash-2',
								handler: () => (showDeleteDialog = true),
							},
						]"
					/>
				</div>
			</template>
		</ListView>

		<Dialog
			:options="{
				title: 'Delete Notebook',
				icon: { name: 'trash', appearance: 'danger' },
			}"
			v-model="showDeleteDialog"
			:dismissable="true"
		>
			<template #body-content>
				<p class="text-base text-gray-600">
					Are you sure you want to delete this notebook?
				</p>
			</template>
			<template #actions>
				<Button appearance="white" @click="showDeleteDialog = false">Cancel</Button>
				<Button appearance="danger" @click="handleDelete" :loading="notebook.deleting">
					Yes
				</Button>
			</template>
		</Dialog>
	</div>
</template>
