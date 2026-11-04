// Archived code and frozen JSON resolve resources from the original city root.
const cityRoot = new URL('../', import.meta.url);

export function archiveURL(path) {
  return new URL(path, cityRoot).href;
}

export function archiveFetch(path, options) {
  return globalThis.fetch(archiveURL(path), options);
}
