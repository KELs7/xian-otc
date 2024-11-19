
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```bash
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const PYENV_VIRTUALENV_INIT: string;
	export const LESSOPEN: string;
	export const QT_SCALE_FACTOR: string;
	export const USER: string;
	export const LC_TIME: string;
	export const LANGUAGE: string;
	export const npm_config_user_agent: string;
	export const XDG_SESSION_TYPE: string;
	export const COMPIZ_CONFIG_PROFILE: string;
	export const GIT_ASKPASS: string;
	export const npm_package_devDependencies__sveltejs_vite_plugin_svelte: string;
	export const npm_package_devDependencies_vite: string;
	export const npm_node_execpath: string;
	export const SHLVL: string;
	export const HOME: string;
	export const CHROME_DESKTOP: string;
	export const OLDPWD: string;
	export const DESKTOP_SESSION: string;
	export const TERM_PROGRAM_VERSION: string;
	export const PYENV_SHELL: string;
	export const GIO_LAUNCHED_DESKTOP_FILE: string;
	export const GTK_MODULES: string;
	export const XDG_SEAT_PATH: string;
	export const VSCODE_GIT_ASKPASS_MAIN: string;
	export const npm_package_devDependencies_svelte_check: string;
	export const LC_MONETARY: string;
	export const MANAGERPID: string;
	export const VSCODE_GIT_ASKPASS_NODE: string;
	export const npm_package_scripts_check: string;
	export const SYSTEMD_EXEC_PID: string;
	export const DBUS_SESSION_BUS_ADDRESS: string;
	export const DBUS_STARTER_BUS_TYPE: string;
	export const GSM_SKIP_SSH_AGENT_WORKAROUND: string;
	export const GIO_LAUNCHED_DESKTOP_FILE_PID: string;
	export const COLORTERM: string;
	export const npm_package_devDependencies_typescript: string;
	export const DEBUGINFOD_URLS: string;
	export const UBUNTU_MENUPROXY: string;
	export const CONDA_CHANGEPS1: string;
	export const IM_CONFIG_PHASE: string;
	export const QT_QPA_PLATFORMTHEME: string;
	export const npm_package_scripts_dev: string;
	export const LOGNAME: string;
	export const npm_package_type: string;
	export const _: string;
	export const npm_package_scripts_check_watch: string;
	export const XDG_SESSION_CLASS: string;
	export const MEMORY_PRESSURE_WATCH: string;
	export const USER_ZDOTDIR: string;
	export const npm_config_registry: string;
	export const GTK_OVERLAY_SCROLLING: string;
	export const TERM: string;
	export const PROMPT_EOL_MARK: string;
	export const PATH: string;
	export const SESSION_MANAGER: string;
	export const GDM_LANG: string;
	export const npm_package_name: string;
	export const NODE: string;
	export const XDG_RUNTIME_DIR: string;
	export const LC_ADDRESS: string;
	export const XDG_SESSION_PATH: string;
	export const GDK_BACKEND: string;
	export const npm_config_frozen_lockfile: string;
	export const DISPLAY: string;
	export const LC_TELEPHONE: string;
	export const LANG: string;
	export const XDG_CURRENT_DESKTOP: string;
	export const VSCODE_INJECTION: string;
	export const XAUTHORITY: string;
	export const XDG_SESSION_DESKTOP: string;
	export const SBX_CHROME_API_RQ: string;
	export const LS_COLORS: string;
	export const TERM_PROGRAM: string;
	export const VSCODE_GIT_IPC_HANDLE: string;
	export const npm_lifecycle_script: string;
	export const XDG_GREETER_DATA_DIR: string;
	export const SSH_AUTH_SOCK: string;
	export const ORIGINAL_XDG_CURRENT_DESKTOP: string;
	export const npm_package_devDependencies__sveltejs_kit: string;
	export const SHELL: string;
	export const LC_NAME: string;
	export const npm_package_version: string;
	export const npm_lifecycle_event: string;
	export const NODE_PATH: string;
	export const QT_ACCESSIBILITY: string;
	export const GDMSESSION: string;
	export const npm_package_scripts_build: string;
	export const npm_package_devDependencies_svelte: string;
	export const LESSCLOSE: string;
	export const LC_MEASUREMENT: string;
	export const GPG_AGENT_INFO: string;
	export const LC_IDENTIFICATION: string;
	export const VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
	export const PWD: string;
	export const npm_execpath: string;
	export const XDG_DATA_DIRS: string;
	export const PYENV_ROOT: string;
	export const DBUS_STARTER_ADDRESS: string;
	export const XDG_CONFIG_DIRS: string;
	export const ZDOTDIR: string;
	export const VIRTUAL_ENV_DISABLE_PROMPT: string;
	export const LC_NUMERIC: string;
	export const npm_package_devDependencies__sveltejs_adapter_auto: string;
	export const npm_command: string;
	export const PNPM_SCRIPT_SRC_DIR: string;
	export const MATE_DESKTOP_SESSION_ID: string;
	export const LC_PAPER: string;
	export const npm_package_scripts_preview: string;
	export const MEMORY_PRESSURE_WRITE: string;
	export const PNPM_HOME: string;
	export const QT_FONT_DPI: string;
	export const INIT_CWD: string;
	export const NODE_ENV: string;
}

/**
 * Similar to [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		PYENV_VIRTUALENV_INIT: string;
		LESSOPEN: string;
		QT_SCALE_FACTOR: string;
		USER: string;
		LC_TIME: string;
		LANGUAGE: string;
		npm_config_user_agent: string;
		XDG_SESSION_TYPE: string;
		COMPIZ_CONFIG_PROFILE: string;
		GIT_ASKPASS: string;
		npm_package_devDependencies__sveltejs_vite_plugin_svelte: string;
		npm_package_devDependencies_vite: string;
		npm_node_execpath: string;
		SHLVL: string;
		HOME: string;
		CHROME_DESKTOP: string;
		OLDPWD: string;
		DESKTOP_SESSION: string;
		TERM_PROGRAM_VERSION: string;
		PYENV_SHELL: string;
		GIO_LAUNCHED_DESKTOP_FILE: string;
		GTK_MODULES: string;
		XDG_SEAT_PATH: string;
		VSCODE_GIT_ASKPASS_MAIN: string;
		npm_package_devDependencies_svelte_check: string;
		LC_MONETARY: string;
		MANAGERPID: string;
		VSCODE_GIT_ASKPASS_NODE: string;
		npm_package_scripts_check: string;
		SYSTEMD_EXEC_PID: string;
		DBUS_SESSION_BUS_ADDRESS: string;
		DBUS_STARTER_BUS_TYPE: string;
		GSM_SKIP_SSH_AGENT_WORKAROUND: string;
		GIO_LAUNCHED_DESKTOP_FILE_PID: string;
		COLORTERM: string;
		npm_package_devDependencies_typescript: string;
		DEBUGINFOD_URLS: string;
		UBUNTU_MENUPROXY: string;
		CONDA_CHANGEPS1: string;
		IM_CONFIG_PHASE: string;
		QT_QPA_PLATFORMTHEME: string;
		npm_package_scripts_dev: string;
		LOGNAME: string;
		npm_package_type: string;
		_: string;
		npm_package_scripts_check_watch: string;
		XDG_SESSION_CLASS: string;
		MEMORY_PRESSURE_WATCH: string;
		USER_ZDOTDIR: string;
		npm_config_registry: string;
		GTK_OVERLAY_SCROLLING: string;
		TERM: string;
		PROMPT_EOL_MARK: string;
		PATH: string;
		SESSION_MANAGER: string;
		GDM_LANG: string;
		npm_package_name: string;
		NODE: string;
		XDG_RUNTIME_DIR: string;
		LC_ADDRESS: string;
		XDG_SESSION_PATH: string;
		GDK_BACKEND: string;
		npm_config_frozen_lockfile: string;
		DISPLAY: string;
		LC_TELEPHONE: string;
		LANG: string;
		XDG_CURRENT_DESKTOP: string;
		VSCODE_INJECTION: string;
		XAUTHORITY: string;
		XDG_SESSION_DESKTOP: string;
		SBX_CHROME_API_RQ: string;
		LS_COLORS: string;
		TERM_PROGRAM: string;
		VSCODE_GIT_IPC_HANDLE: string;
		npm_lifecycle_script: string;
		XDG_GREETER_DATA_DIR: string;
		SSH_AUTH_SOCK: string;
		ORIGINAL_XDG_CURRENT_DESKTOP: string;
		npm_package_devDependencies__sveltejs_kit: string;
		SHELL: string;
		LC_NAME: string;
		npm_package_version: string;
		npm_lifecycle_event: string;
		NODE_PATH: string;
		QT_ACCESSIBILITY: string;
		GDMSESSION: string;
		npm_package_scripts_build: string;
		npm_package_devDependencies_svelte: string;
		LESSCLOSE: string;
		LC_MEASUREMENT: string;
		GPG_AGENT_INFO: string;
		LC_IDENTIFICATION: string;
		VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
		PWD: string;
		npm_execpath: string;
		XDG_DATA_DIRS: string;
		PYENV_ROOT: string;
		DBUS_STARTER_ADDRESS: string;
		XDG_CONFIG_DIRS: string;
		ZDOTDIR: string;
		VIRTUAL_ENV_DISABLE_PROMPT: string;
		LC_NUMERIC: string;
		npm_package_devDependencies__sveltejs_adapter_auto: string;
		npm_command: string;
		PNPM_SCRIPT_SRC_DIR: string;
		MATE_DESKTOP_SESSION_ID: string;
		LC_PAPER: string;
		npm_package_scripts_preview: string;
		MEMORY_PRESSURE_WRITE: string;
		PNPM_HOME: string;
		QT_FONT_DPI: string;
		INIT_CWD: string;
		NODE_ENV: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
