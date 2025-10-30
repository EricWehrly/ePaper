/**
 * Application configuration management
 * Handles loading and caching of app-wide settings like app name
 */

let appConfig = null;

/**
 * Load application configuration from settings API
 * @returns {Promise<object>} Application configuration
 */
export async function loadAppConfig() {
  if (appConfig) {
    return appConfig; // Return cached config
  }
  
  try {
    const response = await fetch('/api/settings');
    if (!response.ok) {
      throw new Error('Failed to load settings');
    }
    const settings = await response.json();
    
    appConfig = {
      appName: settings.app_name || 'ePaper', // Fallback to default
      ...settings
    };
    
    return appConfig;
  } catch (error) {
    console.warn('Failed to load app config, using defaults:', error);
    appConfig = { appName: 'ePaper' }; // Fallback
    return appConfig;
  }
}

/**
 * Get the current app name
 * @returns {Promise<string>} Application name
 */
export async function getAppName() {
  const config = await loadAppConfig();
  return config.appName;
}

/**
 * Update the document title with the app name
 */
export async function updatePageTitle() {
  try {
    const appName = await getAppName();
    document.title = appName;
  } catch (error) {
    console.warn('Failed to update page title:', error);
  }
}

/**
 * Update the main heading (h1) with the app name
 */
export async function updateAppHeading() {
  try {
    const appName = await getAppName();
    const heading = document.querySelector('h1');
    if (heading) {
      heading.textContent = appName;
    }
  } catch (error) {
    console.warn('Failed to update app heading:', error);
  }
}