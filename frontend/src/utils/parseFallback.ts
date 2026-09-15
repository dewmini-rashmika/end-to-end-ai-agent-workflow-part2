export function tryParseFallback<T>(raw: string, key?: string): T | null {
  try {
    let clean = raw.trim();
    if (clean.startsWith('```')) {
      const firstNewline = clean.indexOf('\n');
      const lastBackticks = clean.lastIndexOf('```');
      if (firstNewline !== -1 && lastBackticks > firstNewline) {
        clean = clean.substring(firstNewline + 1, lastBackticks).trim();
      }
    }
    const parsed = JSON.parse(clean);
    if (key && parsed[key]) return parsed[key] as T;
    return parsed as T;
  } catch (e) {
    return null;
  }
}
