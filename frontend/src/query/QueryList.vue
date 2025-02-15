<script setup lang="jsx">
import ListView from '@/components/ListView.vue'
import useDataSources from '@/datasource/useDataSources'
import useNotebooks from '@/notebook/useNotebooks'
import { updateDocumentTitle } from '@/utils'
import { Badge } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import NewDialogWithTypes from '@/components/NewDialogWithTypes.vue'
import useQueries from './useQueries'

const queries = useQueries()
queries.reload()

const new_dialog = ref(false)
const router = useRouter()
const sources = useDataSources()
sources.reload()

const newQuery = ref({ dataSource: '', title: '' })
const dataSourceOptions = computed(() => [
	{ label: 'Select a Data Source', value: '' },
	...sources.list.map((s) => ({ label: s.title, value: s.name })),
])
const createDisabled = computed(
	() => !newQuery.value.dataSource || !newQuery.value.title || queries.creating
)
const createQuery = async () => {
	const { dataSource, title } = newQuery.value
	const name = await queries.create({
		data_source: dataSource,
		title,
	})
	newQuery.value = { dataSource: '', title: '' }
	await nextTick()
	router.push({ name: 'QueryBuilder', params: { name } })
}

const StatusCell = (props) => (
	<Badge color={props.row.status == 'Pending Execution' ? 'yellow' : 'green'}>
		{props.row.status}
	</Badge>
)
const columns = [
	{ label: 'Title', key: 'title' },
	{ label: 'Status', key: 'status', cellComponent: StatusCell },
	{ label: 'Chart Type', key: 'chart_type' },
	{ label: 'Data Source', key: 'data_source' },
	{ label: 'ID', key: 'name' },
	{ label: 'Created', key: 'created_from_now' },
]

const pageMeta = ref({ title: 'Queries' })
updateDocumentTitle(pageMeta)

const notebooks = useNotebooks()
notebooks.reload()
async function openQueryEditor(type) {
	if (type === 'notebook') {
		const uncategorized = notebooks.list.find((notebook) => notebook.title === 'Uncategorized')
		const page_name = await notebooks.createPage(uncategorized.name)
		return router.push({
			name: 'NotebookPage',
			params: {
				notebook: uncategorized.name,
				page: page_name,
			},
		})
	}
	const new_query = {}
	if (type === 'visual') new_query.is_assisted_query = 1
	if (type === 'classic') new_query.is_assisted_query = 0
	const query = await queries.create(new_query)
	router.push({
		name: 'QueryBuilder',
		params: { name: query.name },
	})
}

const queryBuilderTypes = ref([
	{
		label: 'Notebook',
		description: 'Create a query using the notebook interface',
		icon: 'book',
		tag: 'beta',
		handler: () => openQueryEditor('notebook'),
	},
	{
		label: 'Visual',
		description: 'Create a query using the visual interface',
		icon: 'box',
		tag: 'beta',
		handler: () => openQueryEditor('visual'),
	},
	{
		label: 'Classic',
		description: 'Create a query using the classic interface',
		icon: 'layout',
		handler: () => openQueryEditor('classic'),
	},
])
</script>

<template>
	<div class="h-full w-full bg-white px-6 py-4">
		<ListView
			title="Queries"
			:actions="[
				{
					label: 'New Query',
					appearance: 'white',
					iconLeft: 'plus',
					handler: () => (new_dialog = true),
				},
			]"
			:columns="columns"
			:data="queries.list"
			:rowClick="({ name }) => router.push({ name: 'QueryBuilder', params: { name } })"
		>
		</ListView>
	</div>

	<NewDialogWithTypes
		v-model:show="new_dialog"
		title="Select Interface Type"
		:types="queryBuilderTypes"
	/>
</template>
