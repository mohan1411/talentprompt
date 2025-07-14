import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchResult {
  id: string;
  score: number;
  summary: string;
  highlights: string[];
}

interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  totalResults: number;
  currentPage: number;
}

const initialState: SearchState = {
  query: '',
  results: [],
  loading: false,
  error: null,
  totalResults: 0,
  currentPage: 1,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setQuery: (state, action: PayloadAction<string>) => {
      state.query = action.payload;
    },
    searchStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    searchSuccess: (state, action: PayloadAction<{ results: SearchResult[]; total: number }>) => {
      state.results = action.payload.results;
      state.totalResults = action.payload.total;
      state.loading = false;
    },
    searchFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    clearSearch: (state) => {
      state.query = '';
      state.results = [];
      state.error = null;
      state.totalResults = 0;
      state.currentPage = 1;
    },
  },
});

export const { setQuery, searchStart, searchSuccess, searchFailure, clearSearch } =
  searchSlice.actions;
export default searchSlice.reducer;