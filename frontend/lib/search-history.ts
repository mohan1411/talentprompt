/**
 * Client-side search history management
 */

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: number;
  filters?: {
    location?: string;
    skills?: string[];
    experience?: { min?: number; max?: number };
  };
  resultsCount?: number;
}

const STORAGE_KEY = 'promtitude_search_history';
const MAX_ITEMS = 20;
const EXPIRY_DAYS = 30;

class SearchHistory {
  /**
   * Save a search to history
   */
  saveSearch(query: string, filters?: any, resultsCount?: number): void {
    if (!query || query.trim().length === 0) return;

    const history = this.getHistory();
    const newItem: SearchHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      query: query.trim(),
      timestamp: Date.now(),
      filters,
      resultsCount,
    };

    // Add to beginning of array
    history.unshift(newItem);

    // Keep only MAX_ITEMS
    if (history.length > MAX_ITEMS) {
      history.splice(MAX_ITEMS);
    }

    // Save to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('Failed to save search history:', error);
    }
  }

  /**
   * Get all search history
   */
  getHistory(): SearchHistoryItem[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return [];

      const history: SearchHistoryItem[] = JSON.parse(stored);
      const cutoffTime = Date.now() - EXPIRY_DAYS * 24 * 60 * 60 * 1000;

      // Filter out expired items
      return history.filter(item => item.timestamp > cutoffTime);
    } catch (error) {
      console.error('Failed to load search history:', error);
      return [];
    }
  }

  /**
   * Get count of recent searches (last 30 days)
   */
  getRecentCount(days: number = 30): number {
    const history = this.getHistory();
    const cutoffTime = Date.now() - days * 24 * 60 * 60 * 1000;
    
    return history.filter(item => item.timestamp > cutoffTime).length;
  }

  /**
   * Get recent searches for display
   */
  getRecentSearches(limit: number = 5): SearchHistoryItem[] {
    return this.getHistory().slice(0, limit);
  }

  /**
   * Clear all search history
   */
  clearHistory(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear search history:', error);
    }
  }

  /**
   * Remove a specific search from history
   */
  removeSearch(id: string): void {
    const history = this.getHistory();
    const filtered = history.filter(item => item.id !== id);
    
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Failed to update search history:', error);
    }
  }
}

// Export singleton instance
export const searchHistory = new SearchHistory();