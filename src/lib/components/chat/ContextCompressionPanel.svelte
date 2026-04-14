<script>
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		getContextState,
		updateContextSettings,
		getContextSegments,
		triggerCompaction,
		rollbackSegment as apiRollbackSegment,
		resetCompression as apiResetCompression
	} from '$lib/apis/context_compression';

	const i18n = getContext('i18n');

	export let chatId;
	export let user;

	let loading = false;
	let state = null;
	let activeSegment = null;
	let segments = [];

	// Settings form
	let settings = {
		enabled: true,
		threshold_messages: 20,
		keep_last_messages: 5,
		threshold_tokens: 4000,
		include_tool_data: true,
		max_segment_age_days: 30,
		max_segments_per_chat: 10
	};

	onMount(async () => {
		if (chatId) {
			await loadState();
			await loadSegments();
		}
	});

	async function loadState() {
		try {
			const token = localStorage.getItem('token');
			state = await getContextState(token, chatId);
			if (state) {
				settings = {
					enabled: state.enabled,
					threshold_messages: state.threshold_messages,
					keep_last_messages: state.keep_last_messages,
					threshold_tokens: state.threshold_tokens,
					include_tool_data: state.include_tool_data,
					max_segment_age_days: state.max_segment_age_days,
					max_segments_per_chat: state.max_segments_per_chat
				};
			}
		} catch (e) {
			console.error('Error loading context state:', e);
		}
	}

	async function loadSegments() {
		try {
			const token = localStorage.getItem('token');
			segments = await getContextSegments(token, chatId);
			if (segments) {
				activeSegment = segments.find(s => s.status === 'active');
			}
		} catch (e) {
			console.error('Error loading segments:', e);
		}
	}

	async function saveSettings() {
		loading = true;
		try {
			const token = localStorage.getItem('token');
			state = await updateContextSettings(token, chatId, settings);
			if (state) {
				toast.success($i18n.t('Settings saved'));
			} else {
				toast.error($i18n.t('Failed to save settings'));
			}
		} catch (e) {
			console.error('Error saving settings:', e);
			toast.error($i18n.t('Error saving settings'));
		} finally {
			loading = false;
		}
	}

	async function handleTriggerCompaction() {
		loading = true;
		try {
			const token = localStorage.getItem('token');
			const result = await triggerCompaction(token, chatId, true);
			if (result) {
				if (result.status === 'success') {
					toast.success(
						$i18n.t('Context compressed: {{before}} → {{after}} tokens', {
							before: result.token_count_before,
							after: result.token_count_after
						})
					);
					await loadSegments();
				} else {
					toast.info($i18n.t(result.message || 'Compaction not needed'));
				}
			} else {
				toast.error($i18n.t('Failed to compress context'));
			}
		} catch (e) {
			console.error('Error triggering compaction:', e);
			toast.error($i18n.t('Error compressing context'));
		} finally {
			loading = false;
		}
	}

	async function handleRollbackSegment() {
		if (!confirm($i18n.t('Are you sure you want to rollback to the previous segment?'))) {
			return;
		}
		loading = true;
		try {
			const token = localStorage.getItem('token');
			const result = await apiRollbackSegment(token, chatId);
			if (result) {
				toast.success($i18n.t('Rolled back to previous segment'));
				await loadSegments();
				await loadState();
			} else {
				toast.error($i18n.t('Failed to rollback'));
			}
		} catch (e) {
			console.error('Error rolling back:', e);
			toast.error($i18n.t('Error rolling back'));
		} finally {
			loading = false;
		}
	}

	async function handleResetCompression() {
		if (!confirm($i18n.t('Are you sure you want to reset all compression data?'))) {
			return;
		}
		loading = true;
		try {
			const token = localStorage.getItem('token');
			const result = await apiResetCompression(token, chatId);
			if (result) {
				toast.success($i18n.t('Compression reset'));
				await loadSegments();
				await loadState();
			} else {
				toast.error($i18n.t('Failed to reset'));
			}
		} catch (e) {
			console.error('Error resetting:', e);
			toast.error($i18n.t('Error resetting'));
		} finally {
			loading = false;
		}
	}

	function formatDate(timestamp) {
		return new Date(timestamp * 1000).toLocaleString();
	}

	function formatCompressionRatio(segment) {
		if (!segment.token_count_after) return 'N/A';
		const ratio = segment.token_count_before / segment.token_count_after;
		return `${ratio.toFixed(1)}x`;
	}
</script>

<div class="flex flex-col gap-4 p-4">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<h3 class="text-lg font-semibold">{$i18n.t('Context Compression')}</h3>
		{#if activeSegment}
			<span class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
				{$i18n.t('Active')}
			</span>
		{/if}
	</div>

	<!-- Enable/Disable Toggle -->
	<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
		<div>
			<div class="font-medium">{$i18n.t('Enable Compression')}</div>
			<div class="text-sm text-gray-500">{$i18n.t('Automatically compress chat context')}</div>
		</div>
		<label class="relative inline-flex items-center cursor-pointer">
			<input
				type="checkbox"
				class="sr-only peer"
				bind:checked={settings.enabled}
				on:change={saveSettings}
				disabled={loading}
			/>
			<div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
		</label>
	</div>

	<!-- Settings -->
	{#if settings.enabled}
		<div class="space-y-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
			<h4 class="font-medium">{$i18n.t('Settings')}</h4>

			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-medium mb-1">
						{$i18n.t('Message Threshold')}
					</label>
					<input
						type="number"
						min="5"
						max="100"
						bind:value={settings.threshold_messages}
						on:change={saveSettings}
						class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
					/>
					<p class="text-xs text-gray-500 mt-1">
						{$i18n.t('Min messages to trigger compression')}
					</p>
				</div>

				<div>
					<label class="block text-sm font-medium mb-1">
						{$i18n.t('Keep Last Messages')}
					</label>
					<input
						type="number"
						min="1"
						max="20"
						bind:value={settings.keep_last_messages}
						on:change={saveSettings}
						class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
					/>
					<p class="text-xs text-gray-500 mt-1">
						{$i18n.t('Recent messages to keep uncompressed')}
					</p>
				</div>
			</div>

			<div>
				<label class="block text-sm font-medium mb-1">
					{$i18n.t('Token Threshold')}
				</label>
				<input
					type="number"
					min="1000"
					max="10000"
					step="500"
					bind:value={settings.threshold_tokens}
					on:change={saveSettings}
					class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
				/>
				<p class="text-xs text-gray-500 mt-1">
					{$i18n.t('Min tokens to trigger compression')}
				</p>
			</div>

			<div class="flex items-center gap-2">
				<input
					type="checkbox"
					id="include_tool_data"
					bind:checked={settings.include_tool_data}
					on:change={saveSettings}
					class="w-4 h-4"
				/>
				<label for="include_tool_data" class="text-sm">
					{$i18n.t('Include tool call data in summary')}
				</label>
			</div>
		</div>
	{/if}

	<!-- Actions -->
	<div class="flex flex-wrap gap-2">
		<button
			on:click={handleTriggerCompaction}
			disabled={loading || !settings.enabled}
			class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{#if loading}
				<span class="animate-spin">⏳</span>
			{:else}
				{$i18n.t('Compress Now')}
			{/if}
		</button>

		{#if activeSegment}
			<button
				on:click={handleRollbackSegment}
				disabled={loading}
				class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
			>
				{$i18n.t('Rollback')}
			</button>
		{/if}

		{#if segments.length > 0}
			<button
				on:click={handleResetCompression}
				disabled={loading}
				class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
			>
				{$i18n.t('Reset')}
			</button>
		{/if}
	</div>

	<!-- Active Segment Info -->
	{#if activeSegment}
		<div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
			<h4 class="font-medium mb-2">{$i18n.t('Current Summary')}</h4>
			<div class="text-sm space-y-1">
				<div class="flex justify-between">
					<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Compression')}:</span>
					<span class="font-medium">{formatCompressionRatio(activeSegment)}</span>
				</div>
				<div class="flex justify-between">
					<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Tokens')}:</span>
					<span class="font-medium">
						{activeSegment.token_count_before} → {activeSegment.token_count_after}
					</span>
				</div>
				<div class="flex justify-between">
					<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Created')}:</span>
					<span class="font-medium">{formatDate(activeSegment.created_at)}</span>
				</div>
			</div>
			{#if activeSegment.summary_text}
				<div class="mt-3 p-2 bg-white dark:bg-gray-800 rounded text-sm">
					{activeSegment.summary_text}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Segments History -->
	{#if segments.length > 0}
		<div class="space-y-2">
			<h4 class="font-medium">{$i18n.t('History')} ({segments.length})</h4>
			<div class="max-h-48 overflow-y-auto space-y-2">
				{#each segments as segment}
					<div class="p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
						<div class="flex items-center justify-between">
							<span class="font-medium">v{segment.version}</span>
							<span class="text-xs px-2 py-0.5 rounded-full
								{segment.status === 'active' ? 'bg-green-100 text-green-800' :
								 segment.status === 'superseded' ? 'bg-gray-100 text-gray-800' :
								 'bg-red-100 text-red-800'}">
								{segment.status}
							</span>
						</div>
						<div class="text-xs text-gray-500 mt-1">
							{formatDate(segment.created_at)} • {formatCompressionRatio(segment)} compression
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
