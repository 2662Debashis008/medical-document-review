import { create } from "zustand";

type ViewKey = "dashboard" | "upload" | "documents" | "review" | "export" | "settings";

interface UiState {
  activeView: ViewKey;
  selectedDocumentId: number | null;
  notice: string | null;
  setActiveView: (view: ViewKey) => void;
  selectDocument: (documentId: number | null) => void;
  setNotice: (notice: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeView: "dashboard",
  selectedDocumentId: null,
  notice: null,
  setActiveView: (activeView) => set({ activeView }),
  selectDocument: (selectedDocumentId) => set({ selectedDocumentId }),
  setNotice: (notice) => set({ notice }),
}));
